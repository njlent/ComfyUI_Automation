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
            "resampling_method": (list(s.RESAMPLING_METHODS.keys()), {"tooltip": "The algorithm used for resizing images. LANCZOS is high quality."}),
            
            # --- NEW OFFSET INPUTS ---
            "x_offset": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1, "tooltip": "Horizontal offset for the foreground image."}),
            "y_offset": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1, "tooltip": "Vertical offset for the foreground image."}),
        }}
    
    def _tensor_to_pil(self, t): return Image.fromarray((t.cpu().numpy() * 255).astype(np.uint8))
    def _pil_to_tensor(self, p): return torch.from_numpy(np.array(p).astype(np.float32) / 255.0).unsqueeze(0)
    
    def process_image(self, image, width, height, blur_radius, resampling_method, x_offset, y_offset):
        resampling_filter = self.RESAMPLING_METHODS.get(resampling_method, Image.Resampling.LANCZOS);
        output_images = []
        
        for img_tensor in image:
            pil_image = self._tensor_to_pil(img_tensor)
            
            # Create the blurred background, fit to canvas size
            background_img = ImageOps.fit(pil_image.copy(), (width, height), resampling_filter)
            if blur_radius > 0:
                background_img = background_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            
            # Create the foreground layer, scaled down to fit within the canvas while maintaining aspect ratio
            overlay_img = pil_image.copy()
            overlay_img.thumbnail((width, height), resampling_filter)
            
            # Calculate the centered paste position
            paste_x = (width - overlay_img.width) // 2
            paste_y = (height - overlay_img.height) // 2

            # --- APPLY THE OFFSETS ---
            # Add the user-defined offsets to the centered position
            final_paste_x = paste_x + x_offset
            final_paste_y = paste_y + y_offset

            # Paste the overlay onto the background at the final calculated position
            background_img.paste(overlay_img, (final_paste_x, final_paste_y), mask=overlay_img.getchannel('A') if 'A' in overlay_img.getbands() else None)
            
            output_images.append(self._pil_to_tensor(background_img))
            
        return (torch.cat(output_images, dim=0),)

class TextOnImage:
    CATEGORY = "Automation/Image"; RETURN_TYPES = ("IMAGE",); FUNCTION = "draw_text"
    
    @classmethod
    def INPUT_TYPES(s):
        # Using a set to find available fonts to avoid duplicates
        font_files = set(["arial.ttf", "verdana.ttf", "tahoma.ttf", "cour.ttf", "times.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"])
        font_dirs = []
        if os.name == 'nt': font_dirs.append(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'))
        elif os.name == 'posix': font_dirs.extend(['/usr/share/fonts/truetype/', '/usr/local/share/fonts/', '~/.fonts/', '/System/Library/Fonts/', '/Library/Fonts/'])
        for directory in font_dirs:
            try:
                if os.path.exists(os.path.expanduser(directory)):
                    for f in os.listdir(os.path.expanduser(directory)):
                        if f.lower().endswith('.ttf'):
                            font_files.add(f)
            except:
                pass

        return {"required": {
            "image": ("IMAGE", {"tooltip": "The image or image batch to draw on."}),
            "text": ("STRING", {"forceInput": True, "tooltip": "The text string or batch of strings to draw."}),
            "font_name": (sorted(list(font_files)), {"tooltip": "The font file to use. More fonts can be added to your system's font directory."}),
            "font_size": ("INT", {"default": 50, "min": 1, "max": 1024, "step": 1, "tooltip": "Font size in pixels."}),
            "font_color": ("STRING", {"default": "255, 255, 255", "tooltip": "Text color in R, G, B format (e.g., '255, 255, 255' for white)."}),
            "wrap_width": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 1, "tooltip": "Maximum width in pixels for text wrapping. Set to 0 to disable wrapping."}),
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

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> str:
        """Helper function to wrap text to a specific pixel width."""
        lines = []
        words = text.split()
        if not words:
            return ""

        current_line = words[0]
        for word in words[1:]:
            # Test if adding the new word exceeds the max_width
            test_line = f"{current_line} {word}"
            # Use textbbox to get the width of the line. Index 2 is the 'right' coordinate.
            if draw.textbbox((0, 0), test_line, font=font)[2] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        return "\n".join(lines)

    def draw_text(self, image, text, font_name, font_size, font_color, wrap_width, x_position, y_position, horizontal_align, vertical_align, margin):
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
            img_tensor = image[i % num_images]
            text_to_draw = text_list[i % num_texts] if text_list else ""
            
            pil_image = Image.fromarray((img_tensor.cpu().numpy() * 255).astype(np.uint8))
            draw = ImageDraw.Draw(pil_image)
            
            # --- APPLY WORD WRAPPING IF ENABLED ---
            if wrap_width > 0:
                final_text = self._wrap_text(text_to_draw, font, wrap_width, draw)
            else:
                final_text = text_to_draw
            
            img_width, img_height = pil_image.size
            
            # Get the bounding box of the (potentially multi-lined) text block
            try: bbox = draw.textbbox((0, 0), final_text, font=font)
            except AttributeError: bbox = (0,0,0,0) # Fallback for older Pillow versions
            
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position based on alignment, margin, and offset
            if horizontal_align == "left": x = margin
            elif horizontal_align == "right": x = img_width - text_width - margin
            else: x = (img_width - text_width) / 2 # center
            
            if vertical_align == "top": y = margin
            elif vertical_align == "bottom": y = img_height - text_height - margin
            else: y = (img_height - text_height) / 2 # center
            
            # Apply final user-defined nudge
            x += x_position
            y += y_position

            # Draw the text on the image
            draw.text((x, y), final_text, font=font, fill=color_tuple)
            output_images.append(torch.from_numpy(np.array(pil_image).astype(np.float32) / 255.0))
            
        return (torch.stack(output_images),)

class PasteTextOnImageBatch:
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "paste_text"
    
    @classmethod
    def INPUT_TYPES(s):
        font_files = set(["arial.ttf", "verdana.ttf", "tahoma.ttf", "cour.ttf", "times.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"])
        font_dirs = []
        if os.name == 'nt': font_dirs.append(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'))
        elif os.name == 'posix': font_dirs.extend(['/usr/share/fonts/truetype/', '/usr/local/share/fonts/', '~/.fonts/', '/System/Library/Fonts/', '/Library/Fonts/'])
        for directory in font_dirs:
            try:
                if os.path.exists(os.path.expanduser(directory)):
                    for f in os.listdir(os.path.expanduser(directory)):
                        if f.lower().endswith('.ttf'):
                            font_files.add(f)
            except: pass

        return {
            "required": {
                "background_image": ("IMAGE", {"tooltip": "The image or image batch to paste the text onto."}),
                "text": ("STRING", {"forceInput": True, "tooltip": "The text string or batch of strings to display."}),
                "font_name": (sorted(list(font_files)), {"tooltip": "The font file to use."}),
                "font_size": ("INT", {"default": 50, "min": 1, "max": 1024, "step": 1}),
                "font_color": ("STRING", {"default": "255, 255, 255, 255", "tooltip": "Text color in R, G, B, A format."}),
                "wrap_width": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 1}),
                "x_position": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "y_position": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "horizontal_align": (["left", "center", "right"],),
                "vertical_align": (["top", "center", "bottom"],),
                "margin": ("INT", {"default": 20, "min": 0, "max": 1024, "step": 1})
            },
            # --- NEW OPTIONAL INPUT ---
            "optional": {
                "text_durations": ("INT", {"forceInput": True, "tooltip": "A list of frame counts to control the duration of each text. If provided, the sum should match the background frame count."})
            }
        }

    # Helper methods are unchanged
    def find_font(self, font_name):
        font_dirs = [];
        if os.name == 'nt': font_dirs.append(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'))
        elif os.name == 'posix': font_dirs.extend(['/usr/share/fonts/truetype/', '/usr/local/share/fonts/', '~/.fonts/', '/System/Library/Fonts/', '/Library/Fonts/'])
        for directory in font_dirs:
            font_path = os.path.join(os.path.expanduser(directory), font_name)
            if os.path.exists(font_path): return font_path
        print(f"ComfyUI_Automation: Font '{font_name}' not found. Falling back to default."); return "DejaVuSans.ttf"

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> str:
        lines = []
        words = text.split()
        if not words: return ""
        current_line = words[0]
        for word in words[1:]:
            test_line = f"{current_line} {word}"
            if draw.textbbox((0, 0), test_line, font=font)[2] <= max_width:
                current_line = test_line
            else: lines.append(current_line); current_line = word
        lines.append(current_line)
        return "\n".join(lines)

    def paste_text(self, background_image, text, font_name, font_size, font_color, wrap_width, x_position, y_position, horizontal_align, vertical_align, margin, text_durations=None):
        num_bg_frames = background_image.shape[0]
        text_list = [text] if isinstance(text, str) else text
        num_texts = len(text_list)
        
        # --- NEW DURATION LOGIC ---
        use_duration_logic = False
        text_index_map = []
        if text_durations is not None and isinstance(text_durations, list) and text_durations:
            use_duration_logic = True
            print("PasteTextOnImage: Using text duration logic.")
            
            # Create a mapping from frame number to text index
            for text_idx, duration in enumerate(text_durations):
                text_index_map.extend([text_idx] * duration)
            
            if len(text_index_map) != num_bg_frames:
                print(f"Warning: Sum of text_durations ({len(text_index_map)}) does not match background frame count ({num_bg_frames}). Text timing may be incorrect.")

        # --- END OF NEW LOGIC ---

        font_path = self.find_font(font_name)
        try: font = ImageFont.truetype(font_path, font_size)
        except IOError: font = ImageFont.load_default()
        
        try:
            color_parts = [int(c.strip()) for c in font_color.split(',')]
            if len(color_parts) == 3: color_parts.append(255)
            color_tuple = tuple(color_parts)
        except: color_tuple = (255, 255, 255, 255)
        
        output_images = []
        # Loop over every frame of the background image
        for i in range(num_bg_frames):
            bg_tensor = background_image[i]

            # Determine which text to use for the current frame
            if use_duration_logic:
                # Use the pre-calculated map to find the correct text index
                if i < len(text_index_map):
                    text_index_to_use = text_index_map[i]
                else:
                    text_index_to_use = text_index_map[-1] # Use last text if durations are too short
                text_to_draw = text_list[text_index_to_use % num_texts] # Modulo for safety if text list is shorter than durations
            else:
                # Default behavior: cycle through texts frame by frame
                text_to_draw = text_list[i % num_texts]

            # The rest of the logic remains the same
            bg_pil = Image.fromarray((bg_tensor.cpu().numpy() * 255).astype(np.uint8)).convert("RGBA")
            text_layer = Image.new('RGBA', bg_pil.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_layer)
            
            final_text = self._wrap_text(text_to_draw, font, wrap_width, draw) if wrap_width > 0 else text_to_draw
            
            layer_width, layer_height = text_layer.size
            try: bbox = draw.textbbox((0, 0), final_text, font=font)
            except AttributeError: bbox = (0,0,0,0)
            
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            if horizontal_align == "left": x = margin
            elif horizontal_align == "right": x = layer_width - text_width - margin
            else: x = (layer_width - text_width) / 2
            
            if vertical_align == "top": y = margin
            elif vertical_align == "bottom": y = layer_height - text_height - margin
            else: y = (layer_height - text_height) / 2
            
            x += x_position
            y += y_position
            
            draw.text((x, y), final_text, font=font, fill=color_tuple)
            composited_image = Image.alpha_composite(bg_pil, text_layer).convert("RGB")
            output_images.append(torch.from_numpy(np.array(composited_image).astype(np.float32) / 255.0))
            
        return (torch.stack(output_images),)

# --- SRT VIDEO NODES ---
class SRTParser:
    CATEGORY = "Automation/Video"
    FUNCTION = "parse_srt"
    
    ### --- PROACTIVE BUG FIX --- ###
    # This setup fixes a common issue where ComfyUI misinterprets list outputs.
    # The new `text_list` output will now work correctly with nodes that expect a list.
    RETURN_TYPES = ("STRING", "INT", "INT", "INT", "INT", "STRING")
    RETURN_NAMES = (
        "text_batch",         # Original (legacy) output
        "start_ms_batch",     # Original output
        "end_ms_batch",       # Original output
        "duration_ms_batch",  # Original output
        "section_count",      # Original output
        "text_list"           # New, correctly formatted list output
    )
    # This tells ComfyUI to treat only the last output as a proper list.
    OUTPUT_IS_LIST = (False, False, False, False, False, True)
    ### --- END OF BUG FIX --- ###

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
        
        # Return data for all 6 outputs. The `tb` list is used for both the old and new text outputs.
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
    CATEGORY = "Automation/Video"; RETURN_TYPES = ("MASK",); RETURN_NAMES = ("mask_timeline",); FUNCTION = "repeat_batch"
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "mask": ("MASK", {}), "repeat_counts": ("INT", {"forceInput": True}), }}
    def repeat_batch(self, mask, repeat_counts):
        num_masks = mask.shape[0]; counts_list = [repeat_counts] if isinstance(repeat_counts, int) else repeat_counts; num_counts = len(counts_list)
        if num_masks == 0 or num_counts == 0 or not any(c > 0 for c in counts_list):
            h, w = (mask.shape[1], mask.shape[2]) if num_masks > 0 else (64, 64); return (torch.zeros((1, h, w)),)
        loop_count = min(num_masks, num_counts) if num_masks > 1 and num_counts > 1 else max(num_masks, num_counts)
        if num_masks > 1 and num_counts > 1 and num_masks != num_counts:
            print(f"MaskBatchRepeater: Warning! Mismatched batch sizes: Masks {num_masks}, Counts {num_counts}. Using shorter length.")
        output_batches = []
        for i in range(loop_count):
            current_mask_tensor = mask[i % num_masks]; current_count = counts_list[i % num_counts]
            if current_count <= 0: continue
            repeated_batch = current_mask_tensor.unsqueeze(0).repeat(current_count, 1, 1); output_batches.append(repeated_batch)
        if not output_batches: h, w = mask.shape[1], mask.shape[2]; return (torch.zeros((1, h, w)),)
        final_timeline = torch.cat(output_batches, dim=0); return (final_timeline,)

class AudioReactivePaster:
    """
    Pastes an overlay image/timeline onto a background video/image batch, with its
    position animated by the amplitude of a single audio signal. This version is
    memory-efficient and uses the correct paste logic with masks.
    """
    CATEGORY = "Automation/Video"
    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("image_timeline", "amplitude_visualization")
    FUNCTION = "process"

    @classmethod
    def INPUT_TYPES(s):
        # (INPUT_TYPES definition is unchanged)
        return {
            "required": {
                "background_image": ("IMAGE", {"tooltip": "The base video or image batch to paste onto."}),
                "overlay_image": ("IMAGE", {"tooltip": "The image or timeline of images to paste. Should match the background's frame count."}),
                "overlay_mask": ("MASK", {"tooltip": "The mask or timeline of masks for the overlay. Should match the overlay_image."}),
                "audio": ("AUDIO", {"tooltip": "The single audio signal to drive the animation for the entire timeline."}),
                "fps": ("INT", {"default": 24, "min": 1, "max": 120, "tooltip": "MUST match the FPS of your background video timeline."}),
                "size": ("INT", {"default": 256, "min": 1, "max": 8192, "step": 8, "tooltip": "The target size (longest side) of the overlay image. Allows for upscaling."}),
                "horizontal_align": (["left", "center", "right"], {"default": "center"}),
                "vertical_align": (["top", "center", "bottom"], {"default": "center"}),
                "margin": ("INT", {"default": 0, "min": 0, "max": 1024, "step": 1}),
                "x_offset": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "y_offset": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "x_strength": ("FLOAT", {"default": 100.0, "min": -2000.0, "max": 2000.0, "step": 0.1}),
                "y_strength": ("FLOAT", {"default": 100.0, "min": -2000.0, "max": 2000.0, "step": 0.1}),
                "smoothing_method": (["Gaussian", "Exponential Moving Average (EMA)", "Simple Moving Average (SMA)", "None"], {"default": "Gaussian"}),
                "gaussian_sigma": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 50.0, "step": 0.1}),
                "ema_span": ("INT", {"default": 10, "min": 1, "max": 200, "step": 1}),
                "sma_window": ("INT", {"default": 3, "min": 1, "max": 50, "step": 1})
            }
        }

    def _tensor_to_pil(self, t): return Image.fromarray((t.cpu().numpy() * 255).astype(np.uint8))
    def _pil_to_tensor_single(self, p): return torch.from_numpy(np.array(p).astype(np.float32) / 255.0)
    def smooth_data(self, d, m, gs, es, sw):
        if m == "Gaussian": return gaussian_filter1d(d, sigma=gs)
        elif m == "Exponential Moving Average (EMA)": return pd.Series(d).ewm(span=es, adjust=True).mean().tolist()
        elif m == "Simple Moving Average (SMA)": return pd.Series(d).rolling(window=sw, center=True, min_periods=1).mean().bfill().ffill().tolist()
        return d

    def process(self, background_image, overlay_image, overlay_mask, audio, fps, size, horizontal_align, vertical_align, margin, x_offset, y_offset, x_strength, y_strength, smoothing_method, gaussian_sigma, ema_span, sma_window):
        
        if isinstance(background_image, list): background_image = background_image[0]
        if isinstance(overlay_image, list): overlay_image = overlay_image[0]
        if isinstance(overlay_mask, list): overlay_mask = overlay_mask[0]
        if isinstance(audio, list): audio = audio[0]

        # Work directly on the input tensor to be memory-efficient
        video_timeline = background_image
        num_video_frames = video_timeline.shape[0]
        num_overlay_frames = overlay_image.shape[0]

        print(f"AudioReactivePaster: Processing a {num_video_frames}-frame timeline.")

        if num_overlay_frames > 1 and num_overlay_frames != num_video_frames:
            print(f"AudioReactivePaster: Warning! Overlay timeline ({num_overlay_frames} frames) does not match background timeline ({num_video_frames} frames).")

        # Audio processing logic
        sample_rate, waveform = audio['sample_rate'], audio['waveform'][0]
        if waveform.shape[0] > 1: waveform = torch.mean(waveform, dim=0, keepdim=True)
        total_audio_samples = waveform.shape[1]; samples_per_frame = int(sample_rate / fps)
        
        if total_audio_samples < samples_per_frame:
            print("AudioReactivePaster: FATAL ERROR - Audio clip is shorter than a single video frame."); return (video_timeline, torch.zeros((1, 100, num_video_frames, 3)))
            
        raw_amplitudes = [torch.max(torch.abs(waveform[0, int(i / fps * sample_rate) : int(i / fps * sample_rate) + samples_per_frame])).item() if int(i / fps * sample_rate) < total_audio_samples else 0 for i in range(num_video_frames)]
        max_amp = max(raw_amplitudes) if raw_amplitudes else 1.0; max_amp = 1.0 if max_amp == 0 else max_amp
        norm_amps = [a / max_amp for a in raw_amplitudes]
        final_amps = self.smooth_data(norm_amps, smoothing_method, gaussian_sigma, ema_span, sma_window)
        
        # Visualization
        viz_img = Image.new('RGB', (num_video_frames, 100), 'white'); viz_draw = ImageDraw.Draw(viz_img)
        for i, amp in enumerate(final_amps): viz_draw.line([(i, 99), (i, 99 - int(amp * 99))], fill='black', width=1)
        viz_tensor = self._pil_to_tensor_single(viz_img).unsqueeze(0)
        
        cw, ch = video_timeline.shape[2], video_timeline.shape[1]

        # Process frame by frame, modifying the input tensor in-place
        for i in range(num_video_frames):
            bg_tensor_frame = video_timeline[i]
            # No need to convert background to RGBA, paste handles it.
            bg_pil = self._tensor_to_pil(bg_tensor_frame)
            amp = final_amps[i]
            
            overlay_idx = i % num_overlay_frames
            pil_overlay = self._tensor_to_pil(overlay_image[overlay_idx])
            pil_mask = self._tensor_to_pil(overlay_mask[i % overlay_mask.shape[0]])
            
            # Resizing logic (allows upscaling)
            if pil_overlay.width > 0 and pil_overlay.height > 0:
                aspect_ratio = pil_overlay.width / pil_overlay.height
                if pil_overlay.width >= pil_overlay.height:
                    new_w = size; new_h = max(1, int(new_w / aspect_ratio))
                else:
                    new_h = size; new_w = max(1, int(new_h * aspect_ratio))
                pil_overlay = pil_overlay.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            pil_mask = pil_mask.resize(pil_overlay.size, Image.Resampling.LANCZOS)
            
            # Positioning logic
            if horizontal_align == "left": x = margin
            elif horizontal_align == "right": x = cw - pil_overlay.width - margin
            else: x = (cw - pil_overlay.width) // 2
            if vertical_align == "top": y = margin
            elif vertical_align == "bottom": y = ch - pil_overlay.height - margin
            else: y = (ch - pil_overlay.height) // 2
            
            fx = int(x + x_offset + (amp * x_strength)); fy = int(y + y_offset + (amp * y_strength))
            
            # --- START OF FIX: Reverted to the correct paste method ---
            # This is the original, correct logic that uses the mask properly.
            bg_pil.paste(pil_overlay, (fx, fy), mask=pil_mask)
            # --- END OF FIX ---
            
            # Write the modified frame back to the original tensor
            video_timeline[i] = self._pil_to_tensor_single(bg_pil)

        # Return the modified input tensor and the visualization
        return (video_timeline, viz_tensor)
    
    
class AnimateTextOnImage:
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "animate_text"
    
    @classmethod
    def INPUT_TYPES(s):
        # (INPUT_TYPES definition is unchanged)
        font_files = set(["arial.ttf", "verdana.ttf", "tahoma.ttf", "cour.ttf", "times.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"])
        font_dirs = []
        if os.name == 'nt': font_dirs.append(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'))
        elif os.name == 'posix': font_dirs.extend(['/usr/share/fonts/truetype/', '/usr/local/share/fonts/', '~/.fonts/', '/System/Library/Fonts/', '/Library/Fonts/'])
        for directory in font_dirs:
            try:
                if os.path.exists(os.path.expanduser(directory)):
                    for f in os.listdir(os.path.expanduser(directory)):
                        if f.lower().endswith('.ttf'): font_files.add(f)
            except: pass

        return {
            "required": {
                "background_image": ("IMAGE", {"tooltip": "The background video timeline to draw the animation on."}),
                "text": ("STRING", {"multiline": True, "forceInput": True, "tooltip": "A single text block or a list of texts to animate in sequence."}),
                "animation_type": (["Typewriter (Character by Character)", "Reveal (Word by Word)"],),
                "animation_duration": ("INT", {"default": 30, "min": 1, "max": 9999, "tooltip": "Duration of the typing/reveal effect for each text block."}),
                "duration_unit": (["Frames", "Percent of Text Duration"], {"default": "Frames", "tooltip": "'Frames': Fixed duration. 'Percent': Duration is a percentage of the text's total display time."}),
                "font_name": (sorted(list(font_files)),),
                "font_size": ("INT", {"default": 50, "min": 1, "max": 1024, "step": 1}),
                "font_color": ("STRING", {"default": "255, 255, 255, 255", "tooltip": "R,G,B,A format for the main text."}),
                "wrap_width": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 1}),
                "style": (["None", "Background Block", "Drop Shadow"], {"default": "None"}),
                "style_color": ("STRING", {"default": "0, 0, 0, 128", "tooltip": "R,G,B,A format for the chosen style."}),
                "bg_padding": ("INT", {"default": 10, "min": 0, "max": 200, "step": 1, "tooltip": "Padding for the Background Block."}),
                "shadow_x_offset": ("INT", {"default": 5, "min": -100, "max": 100, "step": 1, "tooltip": "Horizontal offset for the Drop Shadow."}),
                "shadow_y_offset": ("INT", {"default": 5, "min": -100, "max": 100, "step": 1, "tooltip": "Vertical offset for the Drop Shadow."}),
                "shadow_blur_radius": ("INT", {"default": 5, "min": 0, "max": 100, "step": 1, "tooltip": "Blur radius for the Drop Shadow."}),
                "x_position": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "y_position": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "horizontal_align": (["left", "center", "right"],),
                "vertical_align": (["top", "center", "bottom"],),
                "margin": ("INT", {"default": 20, "min": 0, "max": 1024, "step": 1})
            },
            "optional": {
                "text_durations": ("INT", {"forceInput": True, "tooltip": "A list of frame counts to control the display duration of each text. Required for animating a list of texts."})
            }
        }

    def find_font(self, font_name):
        font_dirs = [];
        if os.name == 'nt': font_dirs.append(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'))
        elif os.name == 'posix': font_dirs.extend(['/usr/share/fonts/truetype/', '/usr/local/share/fonts/', '~/.fonts/', '/System/Library/Fonts/', '/Library/Fonts/'])
        for directory in font_dirs:
            font_path = os.path.join(os.path.expanduser(directory), font_name)
            if os.path.exists(font_path): return font_path
        print(f"ComfyUI_Automation: Font '{font_name}' not found. Falling back to default."); return "DejaVuSans.ttf"

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> str:
        lines = []
        words = text.split()
        if not words: return ""
        current_line = words[0]
        for word in words[1:]:
            test_line = f"{current_line} {word}"
            if draw.textbbox((0, 0), test_line, font=font)[2] <= max_width:
                current_line = test_line
            else: lines.append(current_line); current_line = word
        lines.append(current_line)
        return "\n".join(lines)

    def _parse_color(self, color_string, default_color):
        try:
            parts = [int(c.strip()) for c in color_string.split(',')]
            if len(parts) == 3: parts.append(255)
            return tuple(parts)
        except:
            return default_color

    def animate_text(self, background_image, text, animation_type, animation_duration, duration_unit, font_name, font_size, font_color, wrap_width, style, style_color, bg_padding, shadow_x_offset, shadow_y_offset, shadow_blur_radius, x_position, y_position, horizontal_align, vertical_align, margin, text_durations=None):
        
        output_tensor = background_image
        num_bg_frames = output_tensor.shape[0]

        text_list = [text] if isinstance(text, str) else text
        frame_to_text_info = {}
        font_path = self.find_font(font_name)
        try: font = ImageFont.truetype(font_path, font_size)
        except IOError: font = ImageFont.load_default()
        
        main_color_tuple = self._parse_color(font_color, (255, 255, 255, 255))
        style_color_tuple = self._parse_color(style_color, (0, 0, 0, 128))

        current_frame = 0
        durations = text_durations if (text_durations and isinstance(text_durations, list)) else [num_bg_frames]
        
        temp_draw = ImageDraw.Draw(Image.new('RGBA', (1,1)))
        
        # --- START OF FIX: Calculate max line height ---
        # We use a string with a high ascender and a low descender to find the max possible line height.
        max_height_bbox = temp_draw.textbbox((0,0), "hg", font=font)
        max_line_height = max_height_bbox[3] - max_height_bbox[1]
        # --- END OF FIX ---

        for i, text_item in enumerate(text_list):
            if i >= len(durations): break
            display_duration = durations[i]
            anim_dur = int(display_duration * (animation_duration / 100.0)) if duration_unit == "Percent of Text Duration" else animation_duration
            anim_dur = max(1, min(anim_dur, display_duration))

            final_text = self._wrap_text(text_item, font, wrap_width, temp_draw) if wrap_width > 0 else text_item
            
            animation_steps = []
            if animation_type == "Typewriter (Character by Character)":
                animation_steps = [final_text[:j+1] for j in range(len(final_text))]
            else:
                unwrapped_words = text_item.split()
                animation_steps = [self._wrap_text(" ".join(unwrapped_words[:j+1]), font, wrap_width, temp_draw) if wrap_width > 0 else " ".join(unwrapped_words[:j+1]) for j in range(len(unwrapped_words))]

            num_steps = len(animation_steps)
            frames_per_step = anim_dur / num_steps if num_steps > 0 else float('inf')

            for frame_offset in range(display_duration):
                frame_idx = current_frame + frame_offset
                if frame_idx >= num_bg_frames: break
                text_to_draw = final_text
                if frame_offset < anim_dur and num_steps > 0:
                    step_index = min(int(frame_offset / frames_per_step), num_steps - 1)
                    text_to_draw = animation_steps[step_index]
                frame_to_text_info[frame_idx] = {"full_text_layout": final_text, "draw_text": text_to_draw}
            
            current_frame += display_duration

        canvas_w, canvas_h = output_tensor.shape[2], output_tensor.shape[1]

        for i in range(num_bg_frames):
            text_info = frame_to_text_info.get(i)
            
            if text_info and text_info["draw_text"]:
                bg_tensor_frame = output_tensor[i]
                bg_pil = Image.fromarray((bg_tensor_frame.cpu().numpy() * 255).astype(np.uint8)).convert("RGBA")
                
                full_text_layout = text_info["full_text_layout"]
                current_text = text_info["draw_text"]
                
                temp_draw_for_bbox = ImageDraw.Draw(bg_pil)
                full_bbox = temp_draw_for_bbox.textbbox((0,0), full_text_layout, font=font)
                text_width, text_height = full_bbox[2] - full_bbox[0], full_bbox[3] - full_bbox[1]
                
                if horizontal_align == "left": x = margin
                elif horizontal_align == "right": x = canvas_w - text_width - margin
                else: x = (canvas_w - text_width) / 2
                
                if vertical_align == "top": y = margin
                elif vertical_align == "bottom": y = canvas_h - text_height - margin
                else: y = (canvas_h - text_height) / 2
                
                final_x, final_y = x + x_position, y + y_position

                text_layer = Image.new('RGBA', bg_pil.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(text_layer)

                lines = current_text.split('\n')
                line_y = final_y

                if style == "Background Block" or style == "Drop Shadow":
                    for line in lines:
                        line_bbox = temp_draw_for_bbox.textbbox((0,0), line, font=font)
                        line_width = line_bbox[2] - line_bbox[0]
                        
                        line_x_offset = 0
                        if horizontal_align == "center":
                           line_x_offset = (text_width - line_width) / 2
                        elif horizontal_align == "right":
                           line_x_offset = text_width - line_width
                        line_x = final_x + line_x_offset

                        if style == "Background Block":
                            # --- START OF FIX: Use max_line_height for consistent block height ---
                            bg_x0 = line_x - bg_padding
                            bg_y0 = line_y - bg_padding
                            bg_x1 = line_x + line_width + bg_padding
                            bg_y1 = line_y + max_line_height + bg_padding
                            # --- END OF FIX ---
                            draw.rectangle([bg_x0, bg_y0, bg_x1, bg_y1], fill=style_color_tuple)
                        
                        elif style == "Drop Shadow":
                            shadow_x = line_x + shadow_x_offset
                            shadow_y_line = line_y + shadow_y_offset
                            draw.text((shadow_x, shadow_y_line), line, font=font, fill=style_color_tuple)
                        
                        line_y += max_line_height # Use the consistent height for line spacing

                if style == "Drop Shadow" and shadow_blur_radius > 0:
                    shadow_text_layer = Image.new('RGBA', bg_pil.size, (0, 0, 0, 0))
                    shadow_draw = ImageDraw.Draw(shadow_text_layer)
                    line_y = final_y
                    for line in lines:
                        line_bbox = temp_draw_for_bbox.textbbox((0,0), line, font=font)
                        line_width = line_bbox[2] - line_bbox[0]
                        line_x_offset = (text_width - line_width) / 2 if horizontal_align == "center" else (text_width - line_width) if horizontal_align == "right" else 0
                        line_x = final_x + line_x_offset
                        shadow_draw.text((line_x + shadow_x_offset, line_y + shadow_y_offset), line, font=font, fill=style_color_tuple)
                        line_y += max_line_height
                    
                    shadow_text_layer = shadow_text_layer.filter(ImageFilter.GaussianBlur(radius=shadow_blur_radius))
                    text_layer.paste(shadow_text_layer, mask=shadow_text_layer)

                line_y = final_y
                for line in lines:
                    line_bbox = temp_draw_for_bbox.textbbox((0,0), line, font=font)
                    line_width = line_bbox[2] - line_bbox[0]
                    line_x_offset = (text_width - line_width) / 2 if horizontal_align == "center" else (text_width - line_width) if horizontal_align == "right" else 0
                    line_x = final_x + line_x_offset
                    draw.text((line_x, line_y), line, font=font, fill=main_color_tuple)
                    line_y += max_line_height

                composited_image = Image.alpha_composite(bg_pil, text_layer).convert("RGB")
                output_tensor[i] = torch.from_numpy(np.array(composited_image).astype(np.float32) / 255.0)

        return (output_tensor,)
# --- UTILITY NODES ---
class StringBatchToString:
    CATEGORY = "Automation/Utils"; RETURN_TYPES, RETURN_NAMES = ("STRING",), ("string",); FUNCTION = "convert"
    @classmethod
    def INPUT_TYPES(s): return {"required": { "string_batch": ("STRING", {"forceInput": True}), "separator": ("STRING", {"multiline": False, "default": "\\n\\n"}) }}
    def convert(self, string_batch, separator):
        s = separator.encode().decode('unicode_escape')
        return (s.join(str(i) for i in string_batch) if isinstance(string_batch, list) else (string_batch if isinstance(string_batch, str) else ""),)
    
class ImageSelectorByIndex:
    CATEGORY = "Automation/Image"; RETURN_TYPES = ("IMAGE", "MASK"); RETURN_NAMES = ("image_batch", "mask_batch"); FUNCTION = "select_images"
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "index_batch": ("INT", {"forceInput": True}), "directory_path": ("STRING", {"multiline": False, "default": ""}),
                "file_pattern": ("STRING", {"multiline": False, "default": "face_{}.png"}),
            }, "optional": { "fallback_image": ("IMAGE", {}), }
        }
    def _load_image(self, fp):
        if not os.path.exists(fp): return None, None
        i = Image.open(fp).convert("RGBA")
        img_arr = np.array(i).astype(np.float32) / 255.0; img_t = torch.from_numpy(img_arr)[None,]
        mask_arr = np.array(i.getchannel('A')).astype(np.float32) / 255.0; mask_t = torch.from_numpy(mask_arr)
        return img_t[:, :, :, :3], mask_t
    def select_images(self, index_batch, directory_path, file_pattern, fallback_image=None):
        indices = [index_batch] if isinstance(index_batch, int) else index_batch
        imgs, masks = [], []
        def_img, def_mask = (torch.zeros((1, 64, 64, 3)), torch.zeros((64, 64))) if fallback_image is None else (fallback_image[0].unsqueeze(0), torch.ones((fallback_image.shape[1], fallback_image.shape[2])))
        for idx in indices:
            fn, fp = file_pattern.format(idx), os.path.join(directory_path, file_pattern.format(idx))
            img_t, mask_t = self._load_image(fp)
            if img_t is not None: imgs.append(img_t); masks.append(mask_t)
            else: print(f"ImageSelector: '{fn}' not found. Using fallback."); imgs.append(def_img); masks.append(def_mask)
        if not imgs: return (def_img, def_mask.unsqueeze(0))
        fh, fw = imgs[0].shape[1], imgs[0].shape[2]
        res_imgs, res_masks = [imgs[0]], [masks[0]]
        for i in range(1, len(imgs)):
            pil_img = Image.fromarray((imgs[i].squeeze(0).cpu().numpy()*255).astype(np.uint8)).resize((fw, fh), Image.Resampling.LANCZOS)
            pil_mask = Image.fromarray((masks[i].cpu().numpy()*255).astype(np.uint8)).resize((fw, fh), Image.Resampling.LANCZOS)
            res_imgs.append(torch.from_numpy(np.array(pil_img).astype(np.float32)/255.0).unsqueeze(0))
            res_masks.append(torch.from_numpy(np.array(pil_mask).astype(np.float32)/255.0))
        return (torch.cat(res_imgs, dim=0), torch.stack(res_masks, dim=0))
    
class StringToInteger:
    CATEGORY = "Automation/Utils"; RETURN_TYPES = ("INT",); RETURN_NAMES = ("int_output",); FUNCTION = "convert"
    @classmethod
    def INPUT_TYPES(s): return {"required": { "text": ("STRING", {"forceInput": True}), }}
    def convert(self, text):
        if isinstance(text, str):
            nums = re.findall(r'-?\d+', text); return (int(nums[0]),) if nums else (0,)
        if isinstance(text, list):
            return ([int(n[0]) if (n := re.findall(r'-?\d+', str(i))) else 0 for i in text],)
        return (0,)
        
class StringToListConverter:
    CATEGORY = "Automation/Converters"; RETURN_TYPES, RETURN_NAMES = ("STRING",), ("STRING_LIST",); FUNCTION = "convert"; OUTPUT_IS_LIST = (True,)
    @classmethod
    def INPUT_TYPES(s): return {"required": { "string_literal": ("STRING", {"multiline": True, "forceInput": True}), }}
    def convert(self, string_literal):
        s_parse = string_literal[0] if isinstance(string_literal, list) and string_literal else string_literal
        if not s_parse or not isinstance(s_parse, str): return ([],)
        try:
            p_list = ast.literal_eval(s_parse)
            return ([str(i) for i in p_list],) if isinstance(p_list, list) else ([str(p_list)],)
        except: return ([],)

class ImageMaskBatchCombiner:
    """
    Takes a list of image/mask batches (from an iterated node) and combines
    them into a single, unified batch. This node uses INPUT_IS_LIST = True
    to force ComfyUI to pass the entire list of inputs at once, effectively
    breaking the execution chain and allowing for proper batching downstream.
    """
    # This is the most important line. It tells ComfyUI to pass the
    # entire list of inputs to the function at once, instead of iterating.
    INPUT_IS_LIST = True
    
    CATEGORY = "Automation/Utils"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("combined_image_batch", "combined_mask_batch")
    FUNCTION = "combine"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # The types are still IMAGE and MASK, but ComfyUI will now
                # automatically package them into a list for our function.
                "image_batch": ("IMAGE", ),
                "mask_batch": ("MASK", ),
            }
        }

    def combine(self, image_batch: list, mask_batch: list):
        # Because INPUT_IS_LIST=True, image_batch and mask_batch are GUARANTEED to be lists.
        
        if not image_batch:
            print("Combiner: Received empty image list. Returning empty tensors.")
            return (torch.zeros((1, 64, 64, 3)), torch.zeros((1, 64, 64)))
            
        print(f"Combiner: Received a LIST of {len(image_batch)} image batches. Concatenating into a single batch.")

        # The ImageSelectorByIndex node already ensures all its outputs are the same size.
        # We can therefore safely use torch.cat to join the list of tensors into one.
        try:
            combined_images = torch.cat(image_batch, dim=0)
            combined_masks = torch.cat(mask_batch, dim=0)
            
            print(f"Combiner: Success! Outputting a single batch of shape {combined_images.shape}.")
            
            return (combined_images, combined_masks)
        except Exception as e:
            print(f"Combiner Error: Could not concatenate tensors. This can happen if the images have different sizes. Error: {e}")
            # Fallback to returning the first item to prevent crashing the workflow.
            return (image_batch[0], mask_batch[0])
        
class TransformPaster:
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("composited_image",)
    FUNCTION = "process"

    @classmethod
    def INPUT_TYPES(s):
        # Using a list from a previous node's class definition for consistency
        resampling_methods = ["LANCZOS", "BICUBIC", "BILINEAR", "NEAREST"]
        
        return {
            "required": {
                "background_image": ("IMAGE", {"tooltip": "The base image to paste onto. Only the first image in a batch is used."}),
                "overlay_image": ("IMAGE", {"tooltip": "The image to transform and paste. Only the first image in a batch is used."}),
                "overlay_mask": ("MASK", {"tooltip": "The mask for the overlay. Only the first mask in a batch is used."}),
                "size": ("INT", {"default": 256, "min": 1, "max": 8192, "step": 8, "tooltip": "The target size (longest side) of the overlay image before pasting."}),
                "rotation": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0, "step": 0.1, "round": 0.01, "tooltip": "Rotation of the overlay in degrees."}),
                "x_offset": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1, "tooltip": "Final horizontal position (from center) of the overlay."}),
                "y_offset": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1, "tooltip": "Final vertical position (from center) of the overlay."}),
                "interpolation": (resampling_methods, {"default": "LANCZOS", "tooltip": "The resampling filter to use for transformations. LANCZOS is high quality."}),
            }
        }

    def _tensor_to_pil(self, tensor):
        # Takes a single frame from a tensor batch
        return Image.fromarray((tensor[0].cpu().numpy() * 255).astype(np.uint8))

    def _pil_to_tensor(self, pil_image):
        return torch.from_numpy(np.array(pil_image).astype(np.float32) / 255.0).unsqueeze(0)

    def process(self, background_image, overlay_image, overlay_mask, size, rotation, x_offset, y_offset, interpolation):
        # Convert tensors to PIL Images
        bg_pil = self._tensor_to_pil(background_image)
        overlay_pil = self._tensor_to_pil(overlay_image)
        mask_pil = self._tensor_to_pil(overlay_mask.unsqueeze(-1).repeat(1, 1, 3)) # Convert mask to 3-channel for PIL

        resampling_filter = getattr(Image.Resampling, interpolation, Image.Resampling.LANCZOS)

        # Combine overlay and mask into a single RGBA image
        overlay_rgba = overlay_pil.convert("RGBA")
        overlay_rgba.putalpha(mask_pil.getchannel('L'))

        # 1. Scale the overlay
        if overlay_rgba.width > 0 and overlay_rgba.height > 0:
            aspect_ratio = overlay_rgba.width / overlay_rgba.height
            if overlay_rgba.width >= overlay_rgba.height:
                new_w = size
                new_h = max(1, int(new_w / aspect_ratio))
            else:
                new_h = size
                new_w = max(1, int(new_h * aspect_ratio))
            overlay_rgba = overlay_rgba.resize((new_w, new_h), resample=resampling_filter)

        # 2. Rotate the scaled overlay
        # 'expand=True' is crucial to prevent the corners from being clipped off.
        if rotation != 0:
            overlay_rgba = overlay_rgba.rotate(rotation, resample=resampling_filter, expand=True)
            
        # 3. Paste onto the background
        # Ensure background is RGBA for proper alpha compositing
        bg_rgba = bg_pil.convert("RGBA")
        
        # Calculate the top-left corner for pasting, so the center is at the offset
        canvas_center_x = bg_rgba.width // 2
        canvas_center_y = bg_rgba.height // 2
        
        paste_x = canvas_center_x + x_offset - (overlay_rgba.width // 2)
        paste_y = canvas_center_y + y_offset - (overlay_rgba.height // 2)

        # The 'mask' argument for paste with an RGBA source is the alpha channel of the source itself.
        bg_rgba.paste(overlay_rgba, (paste_x, paste_y), mask=overlay_rgba)

        # Convert back to RGB for standard ComfyUI output and then to a tensor
        final_pil = bg_rgba.convert("RGB")
        output_tensor = self._pil_to_tensor(final_pil)

        return (output_tensor,)