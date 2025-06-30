# File: ComfyUI_Automation/nodes.py (Final Corrected Version)

# --- IMPORTS ---
import feedparser
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
import torch
import io
import os
from PIL import ImageFilter

# --- RSS FEEDER NODE ---
class RssFeedReader:
    CATEGORY = "Automation/RSS"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("raw_output", "formatted_text", "content_batch_1", "content_batch_2")
    FUNCTION = "read_feed"
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"links": ("STRING", {"multiline": True, "default": "", "tooltip": "One or more RSS feed URLs, each on a new line."}),"max_entries": ("INT", {"default": 3, "min": 1, "max": 100, "step": 1, "tooltip": "Max entries to fetch from EACH feed."}),"skip_entries": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1, "tooltip": "Skips the first N entries from each feed."}),"batch_source_1": (["title", "summary", "link"], {"default": "title"}),"batch_source_2": (["title", "summary", "link"], {"default": "summary"}),"output_mode": (["Concatenated String", "Batch Output"], {"default": "Concatenated String"}),}}
    def clean_html(self, r): return re.sub(re.compile('<.*?>'), '', r if r else "")
    def read_feed(self, links, max_entries, skip_entries, batch_source_1, batch_source_2, output_mode):
        urls, raw, fmt, b1, b2 = [u.strip() for u in links.splitlines() if u.strip()], [], [], [], []
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[skip_entries:skip_entries+max_entries]:
                    raw.append(json.dumps(entry, indent=2))
                    t, l, s_html = getattr(entry,'title',''), getattr(entry,'link',''), getattr(entry,'summary','')
                    fmt.append(f"Title: {t}\nLink: {l}\nSummary: {self.clean_html(s_html)}\n---")
                    v1 = getattr(entry, batch_source_1, ''); b1.append(self.clean_html(v1) if batch_source_1 == 'summary' else v1)
                    v2 = getattr(entry, batch_source_2, ''); b2.append(self.clean_html(v2) if batch_source_2 == 'summary' else v2)
            except Exception as e: print(f"ComfyUI_Automation: RSS Error: {e}")
        if output_mode == "Concatenated String": return ("\n---\n".join(raw), "\n".join(fmt), b1, b2)
        else: return (raw, fmt, b1, b2)

# --- WEB SCRAPER NODES ---
class SimpleWebScraper:
    CATEGORY = "Automation/Web"
    RETURN_TYPES, RETURN_NAMES = ("STRING", "STRING"), ("extracted_texts", "image_urls")
    FUNCTION = "scrape_simple"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"url": ("STRING", {"multiline": False, "default": "", "tooltip": "A single URL or a batch of URLs to scrape."})}}
    def _abs(self, b, l): return urljoin(b, l)
    def scrape_simple(self, u):
        ul, at, au = [u] if isinstance(u, str) else u, [], []
        for s in ul:
            if not s: continue
            try:
                r=requests.get(s, headers={'User-Agent':'Mozilla/5.0'}, timeout=10); r.raise_for_status()
                sp=BeautifulSoup(r.content, 'html.parser')
                at.append(sp.body.get_text(separator=' ', strip=True) if sp.body else "")
                for i in sp.find_all('img'):
                    src = i.get('src')
                    if src:
                        a_url = self._abs(s, src)
                        if a_url not in au: au.append(a_url)
            except Exception as e: print(f"ComfyUI_Automation: Scraper Error: {e}")
        return (at, au)

class TargetedWebScraper:
    CATEGORY = "Automation/Web"
    RETURN_TYPES, RETURN_NAMES = ("STRING", "STRING"), ("extracted_text", "image_urls")
    FUNCTION = "scrape_targeted"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"url": ("STRING", {"multiline": False, "default": "", "tooltip": "A single URL or batch of URLs."}),"selectors": ("STRING", {"multiline": True, "default": "body", "tooltip": "CSS selectors for content to extract."}),"ignore_selectors": ("STRING", {"multiline": True, "default": "nav, footer, .ad-container", "tooltip": "CSS selectors for content to remove before extraction."})}}
    def _abs(self, b, l): return urljoin(b, l)
    def scrape_targeted(self, url, selectors, ignore_selectors):
        ul, ft, fi, sl, isl = [url] if isinstance(url, str) else url, [], [], [s.strip() for s in selectors.splitlines() if s.strip()], [s.strip() for s in ignore_selectors.splitlines() if s.strip()]
        if not sl: return ([], [])
        for s_url in ul:
            if not s_url: continue
            try:
                r = requests.get(s_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10); r.raise_for_status()
                sp = BeautifulSoup(r.content, 'html.parser')
                if isl:
                    for ignored in sp.select(','.join(isl)): ignored.decompose()
                for e in sp.select(','.join(sl)):
                    txt = e.get_text(separator=' ', strip=True)
                    if txt: ft.append(txt)
                    for i in e.find_all('img'):
                        src = i.get('src')
                        if src:
                            a_url = self._abs(s_url, src)
                            if a_url not in fi: fi.append(a_url)
            except Exception as e: print(f"ComfyUI_Automation: Scraper Error on {s_url}: {e}")
        return (ft, fi)

# --- IMAGE LOADER NODE ---
class LoadImageFromURL:
    CATEGORY = "Automation/Image"
    RETURN_TYPES, RETURN_NAMES = ("IMAGE", "MASK"), ("image", "mask")
    FUNCTION = "load_image_from_url"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "A single image URL or a batch of URLs."}),"resize_mode": (["Don't Resize (First Image Only)", "Stretch", "Crop (Center)", "Pad (Black)"], {"default": "Pad (Black)"}),"target_width": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),"target_height": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8})}}
    def load_image_from_url(self, image_url, resize_mode, target_width, target_height):
        ul, it, mt = [image_url] if isinstance(image_url, str) else image_url, [], []
        ts = (target_width, target_height)
        for url in ul:
            if not url or not url.strip().startswith(('http://', 'https://')): continue
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20); r.raise_for_status()
                i = Image.open(io.BytesIO(r.content)); om = i.mode
                if resize_mode == "Stretch": i = i.resize(ts, Image.Resampling.LANCZOS)
                elif resize_mode == "Crop (Center)": i = ImageOps.fit(i, ts, Image.Resampling.LANCZOS)
                elif resize_mode == "Pad (Black)":
                    ic = i.copy(); ic.thumbnail(ts, Image.Resampling.LANCZOS)
                    bg = Image.new('RGB', ts, (0, 0, 0)); bg.paste(ic, ((ts[0] - ic.width) // 2, (ts[1] - ic.height) // 2)); i = bg
                i = i.convert("RGB"); it.append(torch.from_numpy(np.array(i).astype(np.float32) / 255.0)[None,])
                if om == 'RGBA':
                    m = np.array(Image.open(io.BytesIO(r.content)).getchannel('A')).astype(np.float32) / 255.0
                    if resize_mode != "Don't Resize (First Image Only)":
                        mi = Image.fromarray(m); mi = mi.resize(ts, Image.Resampling.LANCZOS); m = np.array(mi)
                    mt.append(torch.from_numpy(m))
                else: mt.append(torch.ones((i.height, i.width), dtype=torch.float32))
                if resize_mode == "Don't Resize (First Image Only)": break
            except Exception as e: print(f"ComfyUI_Automation: Image Load Error on {url}: {e}")
        if not it: return (torch.zeros((1, 64, 64, 3)), torch.zeros((1, 64, 64)))
        return (torch.cat(it, dim=0), torch.cat(mt, dim=0))

# --- SRT VIDEO NODES ---
class SRTParser:
    CATEGORY = "Automation/Video"
    RETURN_TYPES, RETURN_NAMES = ("STRING", "INT", "INT", "INT", "INT"), ("text_batch", "start_ms_batch", "end_ms_batch", "duration_ms_batch", "section_count")
    FUNCTION = "parse_srt"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"srt_content": ("STRING", {"multiline": True}), "handle_pauses": (["Include Pauses", "Ignore Pauses"], {"default": "Include Pauses"})}}
    def srt_time_to_ms(self, t_str): h, m, s, ms = map(int, re.split('[:,]', t_str)); return (h * 3600 + m * 60 + s) * 1000 + ms
    def parse_srt(self, srt_content, handle_pauses):
        p = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\n([\s\S]*?(?=\n\n|\Z))')
        tb, sb, eb, db, let = [], [], [], [], 0
        for m in list(p.finditer(srt_content)):
            txt, s_str, e_str = m.group(4).strip().replace('\n', ' '), m.group(2), m.group(3)
            s_ms, e_ms = self.srt_time_to_ms(s_str), self.srt_time_to_ms(e_str)
            if handle_pauses == "Include Pauses" and s_ms > let:
                pd = s_ms - let
                if pd > 50: tb.append(""); sb.append(let); eb.append(s_ms); db.append(pd)
            tb.append(txt); sb.append(s_ms); eb.append(e_ms); db.append(e_ms - s_ms); let = e_ms
        return (tb, sb, eb, db, len(tb))

class SRTSceneGenerator:
    CATEGORY = "Automation/Video"
    RETURN_TYPES, RETURN_NAMES = ("IMAGE", "INT", "INT"), ("image_timeline", "start_frame_indices", "frame_counts")
    FUNCTION = "generate_scenes"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"duration_ms_batch": ("INT", {"forceInput": True}), "fps": ("INT", {"default": 24}), "width": ("INT", {"default": 512, "step": 8}), "height": ("INT", {"default": 512, "step": 8})}}
    
    # CORRECTED FUNCTION DEFINITION
    def generate_scenes(self, duration_ms_batch, fps, width, height):
        if not isinstance(duration_ms_batch, list) or not duration_ms_batch:
            return (torch.zeros((1, height, width, 3)), [0], [0])
            
        image_batch_list, start_frame_indices, frame_counts, current_frame_index = [], [], [], 0
        
        for duration_ms in duration_ms_batch:
            num_frames = round((duration_ms / 1000.0) * fps)
            if num_frames <= 0: continue
            
            scene_batch = torch.zeros((1, height, width, 3), dtype=torch.float32).repeat(num_frames, 1, 1, 1)
            image_batch_list.append(scene_batch)
            start_frame_indices.append(current_frame_index)
            frame_counts.append(num_frames)
            current_frame_index += num_frames
            
        if not image_batch_list:
            return (torch.zeros((1, height, width, 3)), [0], [0])
            
        return (torch.cat(image_batch_list, dim=0), start_frame_indices, frame_counts)

# --- UTILITY AND MANIPULATION NODES ---
class StringBatchToString:
    CATEGORY = "Automation/Utils"
    RETURN_TYPES, RETURN_NAMES = ("STRING",), ("string",)
    FUNCTION = "convert"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"string_batch": ("STRING", {"forceInput": True}), "separator": ("STRING", {"multiline": False, "default": "\\n\\n"})}}
    def convert(self, string_batch, separator):
        s = separator.encode().decode('unicode_escape')
        if isinstance(string_batch, list): return (s.join(string_batch),)
        elif isinstance(string_batch, str): return (string_batch,)
        return ("",)

class TextOnImage:
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "draw_text"
    @classmethod
    def INPUT_TYPES(s):
        font_files = ["arial.ttf", "verdana.ttf", "tahoma.ttf", "cour.ttf", "times.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
        return {"required": {"image": ("IMAGE",), "text": ("STRING", {"forceInput": True}), "font_name": (font_files,), "font_size": ("INT", {"default": 50}), "font_color": ("STRING", {"default": "255, 255, 255"}), "x_position": ("INT", {"default": 0}), "y_position": ("INT", {"default": 0}), "horizontal_align": (["left", "center", "right"],), "vertical_align": (["top", "center", "bottom"],), "margin": ("INT", {"default": 20})}}

    def find_font(self, font_name):
        font_dirs = []
        if os.name == 'nt': font_dirs.append(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'))
        elif os.name == 'posix': font_dirs.extend(['/usr/share/fonts/truetype/', '/usr/local/share/fonts/', '~/.fonts/', '/System/Library/Fonts/', '/Library/Fonts/'])
        for directory in font_dirs:
            font_path = os.path.join(os.path.expanduser(directory), font_name)
            if os.path.exists(font_path): return font_path
        print(f"ComfyUI_Automation: Font '{font_name}' not found. Falling back to default.")
        return "DejaVuSans.ttf"

    def draw_text(self, image, text, font_name, font_size, font_color, x_position, y_position, horizontal_align, vertical_align, margin):
        num_images = image.shape[0]
        text_list = [text] if isinstance(text, str) else text
        num_texts = len(text_list)
        loop_count = max(num_images, num_texts)
        if num_images > 1 and num_texts > 1: loop_count = min(num_images, num_texts)
        
        font_path = self.find_font(font_name)
        try: font = ImageFont.truetype(font_path, font_size)
        except IOError: font = ImageFont.load_default()
        
        try: color_tuple = tuple(map(int, font_color.split(',')))
        except: color_tuple = (255, 255, 255)
        
        output_images = []
        for i in range(loop_count):
            img_tensor = image[i % num_images]
            text_to_draw = text_list[i % num_texts] if text_list else ""
            
            pil_image = Image.fromarray((img_tensor.cpu().numpy() * 255).astype(np.uint8))
            draw = ImageDraw.Draw(pil_image)
            
            img_width, img_height = pil_image.size
            try: bbox = draw.textbbox((0, 0), text_to_draw, font=font)
            except AttributeError: bbox = (0,0,0,0) # Fallback
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            if horizontal_align == "left": x = margin + x_position
            elif horizontal_align == "right": x = img_width - text_width - margin + x_position
            else: x = (img_width - text_width) / 2 + x_position
            
            if vertical_align == "top": y = margin + y_position
            elif vertical_align == "bottom": y = img_height - text_height - margin + y_position
            else: y = (img_height - text_height) / 2 + y_position
            
            draw.text((x, y), text_to_draw, font=font, fill=color_tuple)
            output_images.append(torch.from_numpy(np.array(pil_image).astype(np.float32) / 255.0))
            
        return (torch.stack(output_images),)
    
class ImageBatchRepeater:
    """
    Repeats images from a batch a specified number of times.
    Designed to work with the SRT Scene Generator's 'frame_counts' output
    to assemble generated content into a video timeline.
    """
    CATEGORY = "Automation/Video"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image_timeline",)
    FUNCTION = "repeat_batch"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "The image or batch of images to repeat."}),
                "repeat_counts": ("INT", {"forceInput": True, "tooltip": "An integer or a list of integers (like 'frame_counts' from SRT Scene Generator) specifying how many times to repeat the corresponding image."}),
            }
        }

    def repeat_batch(self, image, repeat_counts):
        # --- Input Normalization ---
        num_images = image.shape[0]
        
        counts_list = [repeat_counts] if isinstance(repeat_counts, int) else repeat_counts
        num_counts = len(counts_list)

        # --- Edge Case Handling ---
        if num_images == 0 or num_counts == 0 or not any(c > 0 for c in counts_list):
            print("ImageBatchRepeater: No valid images or positive counts provided. Returning a single black frame.")
            h, w = (image.shape[1], image.shape[2]) if num_images > 0 else (512, 512)
            return (torch.zeros((1, h, w, 3)),)

        # --- Determine Loop Count for Smart Batching ---
        loop_count = 1
        # If either input is a batch, we need to loop
        if num_images > 1 or num_counts > 1:
            loop_count = max(num_images, num_counts)
        # If both are batches, they must be paired 1-to-1. Use the shorter length.
        if num_images > 1 and num_counts > 1:
            if num_images != num_counts:
                print(f"ImageBatchRepeater: Warning! Mismatched batch sizes. Images: {num_images}, Counts: {num_counts}. Using the shorter length of {min(num_images, num_counts)}.")
            loop_count = min(num_images, num_counts)
            
        output_batches = []

        # --- Main Repetition Loop ---
        for i in range(loop_count):
            # Use modulo to safely handle single items paired with batches
            current_image_tensor = image[i % num_images]
            current_count = counts_list[i % num_counts]

            if current_count <= 0:
                continue  # Skip if the count is zero or negative

            # Add a batch dimension to the single image tensor for repeating
            # shape goes from (H, W, C) to (1, H, W, C)
            current_image_tensor_unsqueezed = current_image_tensor.unsqueeze(0)
            
            # Use torch.repeat to efficiently duplicate the tensor
            repeated_batch = current_image_tensor_unsqueezed.repeat(current_count, 1, 1, 1)
            
            output_batches.append(repeated_batch)

        if not output_batches:
            print("ImageBatchRepeater: All repeat counts were zero or invalid. Returning a single black frame.")
            h, w = image.shape[1], image.shape[2]
            return (torch.zeros((1, h, w, 3)),)
            
        # Concatenate all the repeated mini-batches into one final timeline
        final_timeline = torch.cat(output_batches, dim=0)

        print(f"ImageBatchRepeater: Created a new timeline of {final_timeline.shape[0]} frames.")
        
        return (final_timeline,)
    
class LayeredImageProcessor:
    """
    Creates a layered image effect by placing a padded version of the input image
    on top of a blurred, cropped, and full-screen version of the same image.
    This node is fully batch-aware.
    """
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "process_image"

    # A map to convert string selection to Pillow's resampling enums
    RESAMPLING_METHODS = {
        "LANCZOS": Image.Resampling.LANCZOS,
        "BICUBIC": Image.Resampling.BICUBIC,
        "BILINEAR": Image.Resampling.BILINEAR,
        "NEAREST": Image.Resampling.NEAREST,
    }

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8, "tooltip": "The final width of the output canvas."}),
                "height": ("INT", {"default": 576, "min": 64, "max": 8192, "step": 8, "tooltip": "The final height of the output canvas."}),
                "blur_radius": ("FLOAT", {"default": 25.0, "min": 0.0, "max": 200.0, "step": 0.1, "tooltip": "The radius for the Gaussian blur on the background layer."}),
                "resampling_method": (list(s.RESAMPLING_METHODS.keys()), {"default": "LANCZOS", "tooltip": "The algorithm used for resizing images."}),
            }
        }

    def _tensor_to_pil(self, tensor):
        """Converts a single image tensor to a PIL Image."""
        return Image.fromarray((tensor.cpu().numpy() * 255).astype(np.uint8))

    def _pil_to_tensor(self, pil_image):
        """Converts a PIL Image to a single image tensor."""
        return torch.from_numpy(np.array(pil_image).astype(np.float32) / 255.0).unsqueeze(0)

    def process_image(self, image, width, height, blur_radius, resampling_method):
        # Get the actual resampling filter from the map
        resampling_filter = self.RESAMPLING_METHODS.get(resampling_method, Image.Resampling.LANCZOS)
        
        output_images = []

        # Loop through each image in the batch
        for img_tensor in image:
            pil_image = self._tensor_to_pil(img_tensor)
            
            # 1. Create the Background Layer
            # Use ImageOps.fit to resize and crop to fill the canvas, preserving aspect ratio
            background_img = ImageOps.fit(pil_image.copy(), (width, height), resampling_filter)
            
            # Apply the blur
            if blur_radius > 0:
                background_img = background_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            
            # 2. Create the Overlay Layer
            overlay_img = pil_image.copy()
            # Use thumbnail to resize down to fit *within* the canvas, preserving aspect ratio
            overlay_img.thumbnail((width, height), resampling_filter)

            # 3. Composite the Layers
            # Calculate the centered position to paste the overlay
            paste_x = (width - overlay_img.width) // 2
            paste_y = (height - overlay_img.height) // 2
            
            # Paste the overlay onto the background.
            # The 'paste' method handles transparency if the overlay has an alpha channel.
            background_img.paste(overlay_img, (paste_x, paste_y), mask=overlay_img.getchannel('A') if 'A' in overlay_img.getbands() else None)

            # Convert the final composited image back to a tensor and add it to our list
            output_images.append(self._pil_to_tensor(background_img))

        # Stack all the processed images into a single output batch
        final_batch = torch.cat(output_images, dim=0)
        
        return (final_batch,)