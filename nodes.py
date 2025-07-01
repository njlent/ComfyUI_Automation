# File: ComfyUI_Automation/nodes.py (Final Version with All Features and Tooltips)

# --- IMPORTS ---
import feedparser
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import numpy as np
import torch
import io
import os
import re
import pandas as pd
from scipy.ndimage import gaussian_filter1d
import ast

# --- RSS FEEDER NODE ---
class RssFeedReader:
    CATEGORY = "Automation/RSS"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("raw_output_batch", "formatted_text_batch", "content_batch_1", "content_batch_2")
    FUNCTION = "read_feed"

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "links": ("STRING", {"multiline": True, "default": "", "tooltip": "One or more RSS feed URLs, each on a new line."}),
            "max_entries": ("INT", {"default": 3, "min": 1, "max": 100, "step": 1, "tooltip": "The maximum number of entries to fetch from EACH feed in the list."}),
            "skip_entries": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1, "tooltip": "Skips the first N entries from each feed. Useful for pagination."}),
            "batch_source_1": (["title", "summary", "link"], {"default": "title", "tooltip": "Select the content for the first batch output."}),
            "batch_source_2": (["title", "summary", "link"], {"default": "summary", "tooltip": "Select the content for the second batch output."}),
            "output_mode": (["Concatenated String", "Batch Output"], {"default": "Batch Output", "tooltip": "Batch Output: Return lists for all outputs. Concatenated String: Join raw/formatted text into single strings."}),
        }}
    
    def clean_html(self, r): return re.sub(re.compile('<.*?>'), '', r if r else "")
    
    def read_feed(self, links, max_entries, skip_entries, batch_source_1, batch_source_2, output_mode):
        urls, raw, fmt, b1, b2 = [u.strip() for u in links.splitlines() if u.strip()], [], [], [], []
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[skip_entries:skip_entries+max_entries]:
                    raw.append(json.dumps(entry, indent=2)); t, l, s_html = getattr(entry,'title',''), getattr(entry,'link',''), getattr(entry,'summary','')
                    fmt.append(f"Title: {t}\nLink: {l}\nSummary: {self.clean_html(s_html)}\n---")
                    v1 = getattr(entry, batch_source_1, ''); b1.append(self.clean_html(v1) if batch_source_1 == 'summary' else v1)
                    v2 = getattr(entry, batch_source_2, ''); b2.append(self.clean_html(v2) if batch_source_2 == 'summary' else v2)
            except Exception as e: print(f"ComfyUI_Automation: RSS Error: {e}")
        if output_mode == "Concatenated String": return ("\n---\n".join(raw), "\n".join(fmt), b1, b2)
        else: return (raw, fmt, b1, b2)

# --- WEB SCRAPER NODES ---
class SimpleWebScraper:
    CATEGORY = "Automation/Web"; RETURN_TYPES, RETURN_NAMES = ("STRING", "STRING"), ("extracted_texts_batch", "image_urls_batch"); FUNCTION = "scrape_simple"
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"url": ("STRING", {"multiline": False, "default": "", "tooltip": "A single URL or a batch of URLs to scrape."})}}
    
    def _abs(self, b, l): return urljoin(b, l)
    def scrape_simple(self, u):
        ul, at, au = [u] if isinstance(u, str) else u, [], [];
        for s in ul:
            if not s: continue
            try:
                r=requests.get(s, headers={'User-Agent':'Mozilla/5.0'}, timeout=10); r.raise_for_status()
                sp=BeautifulSoup(r.content, 'html.parser')
                at.append(sp.body.get_text(separator=' ', strip=True) if sp.body else "")
                for i in sp.find_all('img'):
                    src = i.get('src');
                    if src: a_url = self._abs(s, src);
                    if a_url not in au: au.append(a_url)
            except Exception as e: print(f"ComfyUI_Automation: Scraper Error: {e}")
        return (at, au)

class TargetedWebScraper:
    CATEGORY = "Automation/Web"; RETURN_TYPES, RETURN_NAMES = ("STRING", "STRING"), ("extracted_text_batch", "image_urls_batch"); FUNCTION = "scrape_targeted"
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "url": ("STRING", {"multiline": False, "default": "", "tooltip": "A single URL or batch of URLs."}),
            "selectors": ("STRING", {"multiline": True, "default": "body", "tooltip": "CSS selectors for content to extract. Use browser 'Inspect' tool to find."}),
            "ignore_selectors": ("STRING", {"multiline": True, "default": "nav, footer, .ad-container", "tooltip": "CSS selectors for content to remove before extraction. Cleans the page first."})
        }}
    
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

# --- IMAGE LOADER NODES ---
class LoadImageFromURL:
    CATEGORY = "Automation/Image"; RETURN_TYPES, RETURN_NAMES = ("IMAGE", "MASK"), ("image", "mask"); FUNCTION = "load_image_from_url"
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "A single image URL or a batch of URLs to download."}),
            "resize_mode": (["Don't Resize (First Image Only)", "Stretch", "Crop (Center)", "Pad (Black)"], {"default": "Pad (Black)", "tooltip": "How to handle images of different sizes. 'Don't Resize' is not batch-compatible."}),
            "target_width": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8, "tooltip": "The width all images will be resized to (unless 'Don't Resize' is selected)."}),
            "target_height": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8, "tooltip": "The height all images will be resized to (unless 'Don't Resize' is selected)."})
        }}
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
                    if resize_mode != "Don't Resize (First Image Only)": mi = Image.fromarray(m); mi = mi.resize(ts, Image.Resampling.LANCZOS); m = np.array(mi)
                    mt.append(torch.from_numpy(m))
                else: mt.append(torch.ones((i.height, i.width), dtype=torch.float32))
                if resize_mode == "Don't Resize (First Image Only)": break
            except Exception as e: print(f"ComfyUI_Automation: Image Load Error on {url}: {e}")
        if not it: return (torch.zeros((1, 64, 64, 3)), torch.zeros((1, 64, 64)))
        return (torch.cat(it, dim=0), torch.cat(mt, dim=0))

class LayeredImageProcessor:
    CATEGORY = "Automation/Image"; RETURN_TYPES = ("IMAGE",); RETURN_NAMES = ("image",); FUNCTION = "process_image"
    RESAMPLING_METHODS = {"LANCZOS": Image.Resampling.LANCZOS, "BICUBIC": Image.Resampling.BICUBIC, "BILINEAR": Image.Resampling.BILINEAR, "NEAREST": Image.Resampling.NEAREST}
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "image": ("IMAGE", {"tooltip": "The source image or image batch to process."}),
            "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8, "tooltip": "The final width of the output canvas."}),
            "height": ("INT", {"default": 576, "min": 64, "max": 8192, "step": 8, "tooltip": "The final height of the output canvas."}),
            "blur_radius": ("FLOAT", {"default": 25.0, "min": 0.0, "max": 200.0, "step": 0.1, "tooltip": "The radius for the Gaussian blur on the background layer."}),
            "resampling_method": (list(s.RESAMPLING_METHODS.keys()), {"tooltip": "The algorithm used for resizing images. LANCZOS is high quality."})
        }}
    
    def _tensor_to_pil(self, t): return Image.fromarray((t.cpu().numpy() * 255).astype(np.uint8))
    def _pil_to_tensor(self, p): return torch.from_numpy(np.array(p).astype(np.float32) / 255.0).unsqueeze(0)
    
    def process_image(self, image, width, height, blur_radius, resampling_method):
        resampling_filter = self.RESAMPLING_METHODS.get(resampling_method, Image.Resampling.LANCZOS); output_images = []
        for img_tensor in image:
            pil_image = self._tensor_to_pil(img_tensor)
            background_img = ImageOps.fit(pil_image.copy(), (width, height), resampling_filter)
            if blur_radius > 0: background_img = background_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            overlay_img = pil_image.copy(); overlay_img.thumbnail((width, height), resampling_filter)
            paste_x = (width - overlay_img.width) // 2; paste_y = (height - overlay_img.height) // 2
            background_img.paste(overlay_img, (paste_x, paste_y), mask=overlay_img.getchannel('A') if 'A' in overlay_img.getbands() else None)
            output_images.append(self._pil_to_tensor(background_img))
        return (torch.cat(output_images, dim=0),)

class TextOnImage:
    CATEGORY = "Automation/Image"; RETURN_TYPES = ("IMAGE",); FUNCTION = "draw_text"
    @classmethod
    def INPUT_TYPES(s):
        font_files = ["arial.ttf", "verdana.ttf", "tahoma.ttf", "cour.ttf", "times.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
        return {"required": {
            "image": ("IMAGE", {"tooltip": "The image or image batch to draw on."}),
            "text": ("STRING", {"forceInput": True, "tooltip": "The text string or batch of strings to draw."}),
            "font_name": (font_files, {"tooltip": "The font file to use. Must be installed on your system."}),
            "font_size": ("INT", {"default": 50, "min": 1, "max": 1024, "step": 1, "tooltip": "Font size in pixels."}),
            "font_color": ("STRING", {"default": "255, 255, 255", "tooltip": "Text color in R, G, B format (e.g., '255, 255, 255' for white)."}),
            "x_position": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1, "tooltip": "Horizontal nudge from the aligned position."}),
            "y_position": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1, "tooltip": "Vertical nudge from the aligned position."}),
            "horizontal_align": (["left", "center", "right"], {"tooltip": "Horizontal alignment anchor for the text block."}),
            "vertical_align": (["top", "center", "bottom"], {"tooltip": "Vertical alignment anchor for the text block."}),
            "margin": ("INT", {"default": 20, "min": 0, "max": 1024, "step": 1, "tooltip": "Padding from the edge of the image for alignment."})
        }}
    def find_font(self, font_name):
        font_dirs = [];
        if os.name == 'nt': font_dirs.append(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'))
        elif os.name == 'posix': font_dirs.extend(['/usr/share/fonts/truetype/', '/usr/local/share/fonts/', '~/.fonts/', '/System/Library/Fonts/', '/Library/Fonts/'])
        for directory in font_dirs:
            font_path = os.path.join(os.path.expanduser(directory), font_name)
            if os.path.exists(font_path): return font_path
        print(f"ComfyUI_Automation: Font '{font_name}' not found. Falling back to default."); return "DejaVuSans.ttf"
    def draw_text(self, image, text, font_name, font_size, font_color, x_position, y_position, horizontal_align, vertical_align, margin):
        # ... (rest of the function logic is unchanged)
        num_images = image.shape[0]; text_list = [text] if isinstance(text, str) else text; num_texts = len(text_list)
        loop_count = max(num_images, num_texts)
        if num_images > 1 and num_texts > 1: loop_count = min(num_images, num_texts)
        font_path = self.find_font(font_name)
        try: font = ImageFont.truetype(font_path, font_size)
        except IOError: font = ImageFont.load_default()
        try: color_tuple = tuple(map(int, font_color.split(',')))
        except: color_tuple = (255, 255, 255)
        output_images = []
        for i in range(loop_count):
            img_tensor = image[i % num_images]; text_to_draw = text_list[i % num_texts] if text_list else ""
            pil_image = Image.fromarray((img_tensor.cpu().numpy() * 255).astype(np.uint8)); draw = ImageDraw.Draw(pil_image)
            img_width, img_height = pil_image.size
            try: bbox = draw.textbbox((0, 0), text_to_draw, font=font)
            except AttributeError: bbox = (0,0,0,0)
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

# --- SRT VIDEO NODES ---
class SRTParser:
    CATEGORY = "Automation/Video"
    FUNCTION = "parse_srt"
    
    # --- START OF THE DEFINITIVE FIX ---

    # 1. Define the original 5 outputs PLUS the new 6th output.
    RETURN_TYPES = ("STRING", "INT", "INT", "INT", "INT", "STRING")
    RETURN_NAMES = (
        "text_batch",         # Original output
        "start_ms_batch",     # Original output
        "end_ms_batch",       # Original output
        "duration_ms_batch",  # Original output
        "section_count",      # Original output
        "text_list"           # New, correct list output
    )

    # 2. This is the most important change. We explicitly tell ComfyUI
    #    NOT to treat the first 5 outputs as lists, preserving their
    #    original buggy behavior. We ONLY treat the new 6th output as a list.
    OUTPUT_IS_LIST = (False, False, False, False, False, True)
    
    # --- END OF THE FIX ---

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "srt_content": ("STRING", {"multiline": True, "tooltip": "Paste the entire content of your SRT file here."}),
            "handle_pauses": (["Include Pauses", "Ignore Pauses"], {"default": "Include Pauses", "tooltip": "Determines how to handle silent gaps between subtitle entries."})
        }}

    def srt_time_to_ms(self, t_str):
        h, m, s, ms = map(int, re.split('[:,]', t_str))
        return (h * 3600 + m * 60 + s) * 1000 + ms

    def parse_srt(self, srt_content, handle_pauses):
        # The function logic remains identical.
        p = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\n([\s\S]*?(?=\n\n|\Z))')
        tb, sb, eb, db, let = [], [], [], [], 0
        for m in list(p.finditer(srt_content)):
            txt, s_str, e_str = m.group(4).strip().replace('\n', ' '), m.group(2), m.group(3)
            s_ms, e_ms = self.srt_time_to_ms(s_str), self.srt_time_to_ms(e_str)
            if handle_pauses == "Include Pauses" and s_ms > let:
                pd = s_ms - let
                if pd > 50:
                    tb.append("")
                    sb.append(let)
                    eb.append(s_ms)
                    db.append(pd)
            tb.append(txt)
            sb.append(s_ms)
            eb.append(e_ms)
            db.append(e_ms - s_ms)
            let = e_ms
        
        # 3. The return statement now provides data for all 6 outputs.
        #    The `tb` list is returned for both the first (buggy) and last (correct) outputs.
        #    ComfyUI will format them differently based on the OUTPUT_IS_LIST tuple above.
        return (tb, sb, eb, db, len(tb), tb)

class SRTSceneGenerator:
    CATEGORY = "Automation/Video"; RETURN_TYPES, RETURN_NAMES = ("IMAGE", "INT", "INT"), ("image_timeline", "start_frame_indices", "frame_counts"); FUNCTION = "generate_scenes"
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "duration_ms_batch": ("INT", {"forceInput": True, "tooltip": "Connect the 'duration_ms_batch' from an SRT Parser here."}),
            "fps": ("INT", {"default": 24, "min": 1, "max": 120, "tooltip": "Frames per second for the output video timeline."}),
            "width": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8, "tooltip": "Width of the video frames."}),
            "height": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8, "tooltip": "Height of the video frames."})
        }}
    def generate_scenes(self, duration_ms_batch, fps, width, height):
        # ... (rest of the function logic is unchanged)
        if not isinstance(duration_ms_batch, list) or not duration_ms_batch: return (torch.zeros((1, height, width, 3)), [0], [0])
        ibl, sfi, fc, cfi = [], [], [], 0
        for d_ms in duration_ms_batch:
            nf = round((d_ms / 1000.0) * fps)
            if nf <= 0: continue
            sb = torch.zeros((1, height, width, 3), dtype=torch.float32).repeat(nf, 1, 1, 1)
            ibl.append(sb); sfi.append(cfi); fc.append(nf); cfi += nf
        if not ibl: return (torch.zeros((1, height, width, 3)), [0], [0])
        return (torch.cat(ibl, dim=0), sfi, fc)

class ImageBatchRepeater:
    CATEGORY = "Automation/Video"; RETURN_TYPES = ("IMAGE",); RETURN_NAMES = ("image_timeline",); FUNCTION = "repeat_batch"
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "image": ("IMAGE", {"tooltip": "The image or batch of images to repeat."}),
            "repeat_counts": ("INT", {"forceInput": True, "tooltip": "An integer or a list of integers (like 'frame_counts' from SRT Scene Generator)."}),
        }}
    def repeat_batch(self, image, repeat_counts):
        # ... (rest of the function logic is unchanged)
        num_images = image.shape[0]; counts_list = [repeat_counts] if isinstance(repeat_counts, int) else repeat_counts; num_counts = len(counts_list)
        if num_images == 0 or num_counts == 0 or not any(c > 0 for c in counts_list):
            h, w = (image.shape[1], image.shape[2]) if num_images > 0 else (512, 512); return (torch.zeros((1, h, w, 3)),)
        loop_count = 1
        if num_images > 1 or num_counts > 1: loop_count = max(num_images, num_counts)
        if num_images > 1 and num_counts > 1:
            if num_images != num_counts: print(f"ImageBatchRepeater: Warning! Mismatched batch sizes: {num_images} vs {num_counts}. Using shorter length.")
            loop_count = min(num_images, num_counts)
        output_batches = []
        for i in range(loop_count):
            current_image_tensor = image[i % num_images]; current_count = counts_list[i % num_counts]
            if current_count <= 0: continue
            repeated_batch = current_image_tensor.unsqueeze(0).repeat(current_count, 1, 1, 1); output_batches.append(repeated_batch)
        if not output_batches: h, w = image.shape[1], image.shape[2]; return (torch.zeros((1, h, w, 3)),)
        final_timeline = torch.cat(output_batches, dim=0); return (final_timeline,)

class MaskBatchRepeater:
    """
    Repeats a batch of MASKS a specified number of times to create a video timeline.
    Designed to work with the SRT Scene Generator's 'frame_counts' output.
    """
    CATEGORY = "Automation/Video"
    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("mask_timeline",)
    FUNCTION = "repeat_batch"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mask": ("MASK", {"tooltip": "The mask or batch of masks to repeat."}),
                "repeat_counts": ("INT", {"forceInput": True, "tooltip": "An integer or a list of integers specifying how many times to repeat each corresponding mask."}),
            }
        }

    def repeat_batch(self, mask, repeat_counts):
        num_masks = mask.shape[0]
        counts_list = [repeat_counts] if isinstance(repeat_counts, int) else repeat_counts
        num_counts = len(counts_list)

        if num_masks == 0 or num_counts == 0 or not any(c > 0 for c in counts_list):
            # Return a default empty mask if inputs are invalid
            h, w = (mask.shape[1], mask.shape[2]) if num_masks > 0 else (64, 64)
            return (torch.zeros((1, h, w)),)

        # Determine the number of iterations for smart batching
        loop_count = min(num_masks, num_counts) if num_masks > 1 and num_counts > 1 else max(num_masks, num_counts)
        if num_masks > 1 and num_counts > 1 and num_masks != num_counts:
            print(f"MaskBatchRepeater: Warning! Mismatched batch sizes: Masks {num_masks}, Counts {num_counts}. Using shorter length.")

        output_batches = []
        for i in range(loop_count):
            # Use specific variable names for clarity
            current_mask_tensor = mask[i % num_masks]
            current_count = counts_list[i % num_counts]
            
            if current_count <= 0:
                continue
            
            # The logic for masks (3 dimensions) is slightly different than for images (4 dimensions)
            # Unsqueeze adds a dimension, so (H, W) -> (1, H, W)
            # Repeat then expands the first dimension, resulting in (N, H, W)
            repeated_batch = current_mask_tensor.unsqueeze(0).repeat(current_count, 1, 1)
            output_batches.append(repeated_batch)

        if not output_batches:
            h, w = mask.shape[1], mask.shape[2]
            return (torch.zeros((1, h, w)),)
            
        final_timeline = torch.cat(output_batches, dim=0)
        print(f"MaskBatchRepeater: Created a new mask timeline of {final_timeline.shape[0]} frames.")
        
        return (final_timeline,)

class AudioReactivePaster:
    """
    Pastes an overlay image onto a background video/image batch, with its
    position animated by the amplitude of an audio signal. Includes multiple advanced
    smoothing methods for high-quality motion.
    """
    CATEGORY = "Automation/Video"
    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("image_timeline", "amplitude_visualization")
    FUNCTION = "process"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "background_image": ("IMAGE", {"tooltip": "The base video or image batch to paste onto."}),
                "overlay_image": ("IMAGE", {"tooltip": "The image to paste. If a batch is provided, only the first image is used."}),
                "overlay_mask": ("MASK", {"tooltip": "The mask for the overlay image. Only the first mask in a batch is used."}),
                "audio": ("AUDIO", {"tooltip": "The audio signal to drive the animation."}),
                "fps": ("INT", {"default": 24, "min": 1, "max": 120, "tooltip": "MUST match the FPS of your background video timeline."}),
                
                # Motion and Position controls
                "size": ("INT", {"default": 256, "min": 1, "max": 8192, "step": 8, "tooltip": "The target size of the overlay image."}),
                "horizontal_align": (["left", "center", "right"], {"default": "center", "tooltip": "Horizontal resting position of the overlay."}),
                "vertical_align": (["top", "center", "bottom"], {"default": "center", "tooltip": "Vertical resting position of the overlay."}),
                "margin": ("INT", {"default": 0, "min": 0, "max": 1024, "step": 1, "tooltip": "Padding from the edge for alignment."}),
                "x_offset": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1, "tooltip": "Static horizontal offset from the aligned position."}),
                "y_offset": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1, "tooltip": "Static vertical offset from the aligned position."}),
                
                # --- UPDATED STRENGTH CONTROLS ---
                "x_strength": ("FLOAT", {
                    "default": 100.0, 
                    "min": -2000.0, 
                    "max": 2000.0, 
                    "step": 0.1, 
                    "tooltip": "How much the audio moves the image horizontally. Use negative values to move left."
                }),
                "y_strength": ("FLOAT", {
                    "default": 100.0, 
                    "min": -2000.0, 
                    "max": 2000.0, 
                    "step": 0.1, 
                    "tooltip": "How much the audio moves the image vertically. Use negative values to move up."
                }),
                
                # Smoothing Controls
                "smoothing_method": (["Gaussian", "Exponential Moving Average (EMA)", "Simple Moving Average (SMA)", "None"], {
                    "default": "Gaussian", "tooltip": "The algorithm used to smooth the audio-driven motion."
                }),
                "gaussian_sigma": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 50.0, "step": 0.1, "tooltip": "Strength for Gaussian smoothing. Higher = smoother. Recommended: 2-10."}),
                "ema_span": ("INT", {"default": 10, "min": 1, "max": 200, "step": 1, "tooltip": "Window for EMA smoothing. Higher = smoother but more 'lag'. Recommended: 5-20."}),
                "sma_window": ("INT", {"default": 3, "min": 1, "max": 50, "step": 1, "tooltip": "Window for Simple Moving Average. Larger values are smoother."})
            }
        }

    # --- NO CHANGES TO THE LOGIC BELOW THIS LINE ---
    def _tensor_to_pil(self, t): return Image.fromarray((t.cpu().numpy() * 255).astype(np.uint8))
    def _pil_to_tensor_single(self, p): return torch.from_numpy(np.array(p).astype(np.float32) / 255.0)
    def smooth_data(self, d, m, gs, es, sw):
        if m == "Gaussian": return gaussian_filter1d(d, sigma=gs)
        elif m == "Exponential Moving Average (EMA)": return pd.Series(d).ewm(span=es, adjust=True).mean().tolist()
        elif m == "Simple Moving Average (SMA)": return pd.Series(d).rolling(window=sw, center=True, min_periods=1).mean().bfill().ffill().tolist()
        return d
    def process(self, background_image, overlay_image, overlay_mask, audio, fps, size, horizontal_align, vertical_align, margin, x_offset, y_offset, x_strength, y_strength, smoothing_method, gaussian_sigma, ema_span, sma_window):
        video_timeline = background_image.clone(); num_video_frames = video_timeline.shape[0]; sample_rate = audio['sample_rate']; waveform = audio['waveform'][0]
        if waveform.shape[0] > 1: waveform = torch.mean(waveform, dim=0, keepdim=True)
        total_audio_samples = waveform.shape[1]; samples_per_frame = int(sample_rate / fps)
        if total_audio_samples < samples_per_frame:
            print("AudioReactivePaster: FATAL ERROR - Audio clip is shorter than a single video frame. Check audio file.")
            return (video_timeline, torch.zeros((1, 100, num_video_frames, 3)))
        raw_amplitudes = []
        for i in range(num_video_frames):
            t_sec = i / fps; s_idx = int(t_sec * sample_rate) % total_audio_samples; s_start = s_idx; s_end = s_start + samples_per_frame
            chunk = waveform[0, s_start:s_end] if s_end <= total_audio_samples else torch.cat((waveform[0, s_start:], waveform[0, :s_end - total_audio_samples]))
            raw_amplitudes.append(torch.max(torch.abs(chunk)).item())
        max_amp = max(raw_amplitudes) if raw_amplitudes else 1.0; max_amp = 1.0 if max_amp == 0 else max_amp
        norm_amps = [a / max_amp for a in raw_amplitudes]
        final_amps = self.smooth_data(norm_amps, smoothing_method, gaussian_sigma, ema_span, sma_window)
        viz_img = Image.new('RGB', (num_video_frames, 100), 'white'); viz_draw = ImageDraw.Draw(viz_img)
        for i, amp in enumerate(final_amps): viz_draw.line([(i, 99), (i, 99 - int(amp * 99))], fill='black', width=1)
        viz_tensor = self._pil_to_tensor_single(viz_img).unsqueeze(0)
        pil_overlay = self._tensor_to_pil(overlay_image[0]); pil_mask = self._tensor_to_pil(overlay_mask[0])
        pil_overlay.thumbnail((size, size), Image.Resampling.LANCZOS); pil_mask = pil_mask.resize(pil_overlay.size, Image.Resampling.LANCZOS)
        cw, ch = video_timeline.shape[2], video_timeline.shape[1]
        for i in range(num_video_frames):
            bg_pil = self._tensor_to_pil(video_timeline[i]); amp = final_amps[i]
            if horizontal_align == "left": x = margin
            elif horizontal_align == "right": x = cw - pil_overlay.width - margin
            else: x = (cw - pil_overlay.width) // 2
            if vertical_align == "top": y = margin
            elif vertical_align == "bottom": y = ch - pil_overlay.height - margin
            else: y = (ch - pil_overlay.height) // 2
            fx = int(x + x_offset + (amp * x_strength)); fy = int(y + y_offset + (amp * y_strength))
            bg_pil.paste(pil_overlay, (fx, fy), mask=pil_mask); video_timeline[i] = self._pil_to_tensor_single(bg_pil)
        return (video_timeline, viz_tensor)

# --- UTILITY NODES ---
# (I moved this down to group it with other manipulation nodes)
class StringBatchToString:
    CATEGORY = "Automation/Utils"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "convert"
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "string_batch": ("STRING", {"forceInput": True, "tooltip": "Connect a list/batch of strings here (e.g., from a scraper)."}),
            "separator": ("STRING", {"multiline": False, "default": "\\n\\n", "tooltip": "The characters to place between each string. Use \\n for a newline."})
        }}
    def convert(self, string_batch, separator):
        s = separator.encode().decode('unicode_escape')
        if isinstance(string_batch, list): return (s.join(str(i) for i in string_batch),)
        elif isinstance(string_batch, str): return (string_batch,)
        return ("",)
    
class ImageSelectorByIndex:
    """
    Selects and loads a batch of images from a directory based on a
    corresponding batch of indices (numbers).
    """
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image_batch", "mask_batch")
    FUNCTION = "select_images"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "index_batch": ("INT", {"forceInput": True, "tooltip": "A list of integers (e.g., from an LLM) used to select the images."}),
                "directory_path": ("STRING", {"multiline": False, "default": "", "tooltip": "The path to the folder containing your numbered image assets."}),
                "file_pattern": ("STRING", {"multiline": False, "default": "face_{}.png", "tooltip": "The naming pattern for your files. Use '{}' as a placeholder for the index number."}),
            },
            "optional": {
                "fallback_image": ("IMAGE", {"tooltip": "An optional image to use if a numbered file is not found. If not provided, a black image is used."}),
            }
        }
        
    def _load_image(self, full_path):
        """Loads a single image and returns its image and mask tensors."""
        if not os.path.exists(full_path):
            return None, None
            
        i = Image.open(full_path)
        i = i.convert("RGBA") # Ensure there's an alpha channel
        
        image = np.array(i).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image)[None,]
        
        img_pil_alpha = i.getchannel('A')
        mask = np.array(img_pil_alpha).astype(np.float32) / 255.0
        mask_tensor = torch.from_numpy(mask)
        
        return image_tensor[:, :, :, :3], mask_tensor # Return RGB and Mask

    def select_images(self, index_batch, directory_path, file_pattern, fallback_image=None):
        # Normalize index_batch to be a list
        indices = [index_batch] if isinstance(index_batch, int) else index_batch
        
        output_images = []
        output_masks = []
        
        # Prepare a default fallback if none is provided
        default_fallback_img = None
        default_fallback_mask = None
        if fallback_image is None:
            # Create a 64x64 transparent pixel as a default fallback
            default_fallback_img = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            default_fallback_mask = torch.zeros((64, 64), dtype=torch.float32)

        for index in indices:
            try:
                # Format the filename using the provided pattern and index
                filename = file_pattern.format(index)
                full_path = os.path.join(directory_path, filename)
                
                img_tensor, mask_tensor = self._load_image(full_path)
                
                if img_tensor is not None:
                    print(f"ImageSelectorByIndex: Loaded '{filename}'")
                    output_images.append(img_tensor)
                    output_masks.append(mask_tensor)
                else:
                    # File was not found, use a fallback
                    print(f"ImageSelectorByIndex: Warning! File '{filename}' not found. Using fallback.")
                    if fallback_image is not None:
                        # Use the first frame of the provided fallback image
                        output_images.append(fallback_image[0].unsqueeze(0))
                        # We don't have a mask for the fallback, so we create an opaque one
                        output_masks.append(torch.ones((fallback_image.shape[1], fallback_image.shape[2]), dtype=torch.float32))
                    else:
                        output_images.append(default_fallback_img)
                        output_masks.append(default_fallback_mask)
                        
            except Exception as e:
                print(f"ImageSelectorByIndex: Error processing index {index}: {e}")
                # On error, also use the fallback
                if fallback_image is not None:
                    output_images.append(fallback_image[0].unsqueeze(0))
                    output_masks.append(torch.ones((fallback_image.shape[1], fallback_image.shape[2]), dtype=torch.float32))
                else:
                    output_images.append(default_fallback_img)
                    output_masks.append(default_fallback_mask)

        if not output_images:
            print("ImageSelectorByIndex: No images were loaded.")
            return (default_fallback_img, default_fallback_mask.unsqueeze(0))

        # We must resize all images to match the first one to create a valid batch
        first_h, first_w = output_images[0].shape[1], output_images[0].shape[2]
        resized_images = [output_images[0]]
        resized_masks = [output_masks[0]]

        for i in range(1, len(output_images)):
            img_tensor = output_images[i]
            mask_tensor = output_masks[i]
            
            # Convert to PIL for resizing
            pil_img = Image.fromarray((img_tensor.squeeze(0).cpu().numpy() * 255).astype(np.uint8))
            pil_mask = Image.fromarray((mask_tensor.cpu().numpy() * 255).astype(np.uint8))
            
            # Resize
            pil_img = pil_img.resize((first_w, first_h), Image.Resampling.LANCZOS)
            pil_mask = pil_mask.resize((first_w, first_h), Image.Resampling.LANCZOS)
            
            # Convert back to tensor
            resized_images.append(torch.from_numpy(np.array(pil_img).astype(np.float32) / 255.0).unsqueeze(0))
            resized_masks.append(torch.from_numpy(np.array(pil_mask).astype(np.float32) / 255.0))

        return (torch.cat(resized_images, dim=0), torch.stack(resized_masks, dim=0))
    
class StringToInteger:
    """
    Converts a string or a batch of strings into an integer or a batch of integers.
    It intelligently handles non-numeric text.
    """
    CATEGORY = "Automation/Utils"
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("int_output",)
    FUNCTION = "convert"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True, "tooltip": "A string or a batch of strings to convert to integers."}),
            }
        }

    def convert(self, text):
        # Handle a single string input
        if isinstance(text, str):
            try:
                # Find all integer numbers in the string
                numbers = re.findall(r'-?\d+', text)
                if numbers:
                    # Return the first number found
                    result = int(numbers[0])
                    print(f"StringToInteger: Converted '{text}' -> {result}")
                    return (result,)
                else:
                    # If no numbers are found, return 0
                    print(f"StringToInteger: No numbers found in '{text}'. Defaulting to 0.")
                    return (0,)
            except ValueError:
                print(f"StringToInteger: Could not convert '{text}' to an integer. Defaulting to 0.")
                return (0,)

        # Handle a batch (list) of strings
        elif isinstance(text, list):
            int_batch = []
            for item in text:
                try:
                    # Find all integer numbers in the string
                    numbers = re.findall(r'-?\d+', str(item)) # Convert item to string just in case
                    if numbers:
                        # Append the first number found
                        int_batch.append(int(numbers[0]))
                    else:
                        # If no numbers are found, append 0
                        int_batch.append(0)
                except ValueError:
                    # If conversion fails for an item, append 0
                    int_batch.append(0)
            
            print(f"StringToInteger: Converted batch of {len(text)} strings to integers.")
            return (int_batch,)
            
        # Fallback for other unexpected types
        else:
            print(f"StringToInteger: Received unexpected type '{type(text)}'. Defaulting to 0.")
            return (0,)
        
class StringToListConverter:
    """
    This node takes a string that is a Python list literal (e.g., "['a', 'b', 'c']")
    and converts it into a proper ComfyUI batch/list output. It's robust enough
    to handle inputs that are either a raw string or a list containing a single string.
    """
    CATEGORY = "Automation/Converters"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING_LIST",)
    FUNCTION = "convert"
    OUTPUT_IS_LIST = (True,)

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "string_literal": ("STRING", {"multiline": True, "forceInput": True}),
            }
        }

    def convert(self, string_literal):
        # THIS IS THE CRUCIAL FIX
        # First, determine the actual string we need to parse.
        string_to_parse = ""
        if isinstance(string_literal, list):
            if string_literal: # If the list is not empty
                string_to_parse = string_literal[0]
        else:
            string_to_parse = string_literal
        
        if not string_to_parse:
            return ([],) # Return an empty list if there's nothing to parse

        try:
            # Safely evaluate the string as a Python literal
            parsed_list = ast.literal_eval(string_to_parse)
            
            # Ensure the result is actually a list
            if not isinstance(parsed_list, list):
                return ([str(parsed_list)],)

            # Ensure all items in the list are strings, as per RETURN_TYPES
            string_list = [str(item) for item in parsed_list]
            return (string_list,)
        except (ValueError, SyntaxError, TypeError) as e:
            # Handle cases where the string is not a valid list literal
            print(f"StringToListConverter Error: Could not parse string '{string_to_parse[:100]}...' as a list. Error: {e}. Returning an empty list.")
            return ([],)