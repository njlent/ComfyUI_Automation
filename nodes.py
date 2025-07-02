# File: ComfyUI_Automation/nodes.py (Final Version with All Features and Tooltips)

# --- IMPORTS ---
import platform # Import platform to detect the OS
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
import torch
import mimetypes
import boto3 # AWS SDK for Python
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import datetime
from pytz import timezone, utc
import gc

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("MemoryPurge Node: `psutil` library not found. RAM usage will not be reported. To enable, run: pip install psutil")

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
            "url": ("STRING", {"multiline": False, "default": "", "tooltip": "A single URL or a batch of URLs to scrape."}),
            "selectors": ("STRING", {"multiline": True, "default": "body", "tooltip": "CSS selectors for the main content areas you want to extract. Use browser 'Inspect' tool. E.g., .article-body, #main-content"}),
            "ignore_selectors": ("STRING", {"multiline": True, "default": "nav, footer, .ad-container", "tooltip": "CSS selectors for content to completely remove before extraction. Each on a new line. E.g., to ignore a div with class 'postTitle', add '.postTitle'."})
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
                
                # --- This is the key logic for ignoring elements ---
                if isl:
                    # Find all elements matching the ignore_selectors and completely remove them from the page.
                    for ignored_element in sp.select(','.join(isl)): 
                        ignored_element.decompose()
                
                # Now, find the main content elements in the cleaned-up page.
                for e in sp.select(','.join(sl)):
                    # Extract text from the main element.
                    txt = e.get_text(separator=' ', strip=True)
                    if txt: ft.append(txt)
                    
                    # Also extract images from within that main element.
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
            
            # --- START OF FIX: Replaced thumbnail() with robust resize logic ---
            # Create the foreground layer, scaling it to fit the canvas while maintaining aspect ratio.
            # This handles both upscaling and downscaling correctly.
            overlay_img = pil_image.copy()
            original_overlay_width, original_overlay_height = overlay_img.size

            # Prevent division by zero if image has no size
            if original_overlay_height > 0 and height > 0:
                # Calculate aspect ratios
                canvas_aspect = width / height
                image_aspect = original_overlay_width / original_overlay_height

                # Determine the new size for the overlay
                if image_aspect > canvas_aspect:
                    # Image is wider than the canvas aspect ratio -> fit to canvas width
                    new_overlay_width = width
                    new_overlay_height = int(new_overlay_width / image_aspect)
                else:
                    # Image is taller than or same as canvas aspect ratio -> fit to canvas height
                    new_overlay_height = height
                    new_overlay_width = int(new_overlay_height * image_aspect)

                # Resize the overlay. The 'resize' method handles both upscaling and downscaling.
                overlay_img = overlay_img.resize((new_overlay_width, new_overlay_height), resampling_filter)
            # --- END OF FIX ---

            # Calculate the centered paste position
            paste_x = (width - overlay_img.width) // 2
            paste_y = (height - overlay_img.height) // 2

            # Apply the user-defined offsets
            final_paste_x = paste_x + x_offset
            final_paste_y = paste_y + y_offset

            # Paste the overlay onto the background
            background_img.paste(overlay_img, (final_paste_x, final_paste_y), mask=overlay_img.getchannel('A') if 'A' in overlay_img.getbands() else None)
            
            output_images.append(self._pil_to_tensor(background_img))
            
        return (torch.cat(output_images, dim=0),)


class TextOnImage:
    CATEGORY = "Automation/Image"; RETURN_TYPES = ("IMAGE",); FUNCTION = "draw_text"
    
    EMOJI_FONT = None
    EMOJI_FONT_LOADED = False
    EMOJI_SPLIT_REGEX = re.compile(
        r'('
        r'['
        '\U0001F1E0-\U0001F1FF'
        '\U0001F300-\U0001F5FF'
        '\U0001F600-\U0001F64F'
        '\U0001F680-\U0001F6FF'
        '\U0001F700-\U0001F77F'
        '\U0001F780-\U0001F7FF'
        '\U0001F800-\U0001F8FF'
        '\U0001F900-\U0001F9FF'
        '\U0001FA00-\U0001FA6F'
        '\U0001FA70-\U0001FAFF'
        '\U00002702-\U000027B0'
        '\U000024C2-\U0001F251'
        ']'
        r')'
    )

    def _get_emoji_font_path(self):
        system = platform.system()
        if system == "Windows":
            return os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'seguiemj.ttf')
        elif system == "Darwin":
            path = "/System/Library/Fonts/Apple Color Emoji.ttc"
            if os.path.exists(path): return path
            return "/System/Library/Fonts/Core/AppleColorEmoji.ttf"
        else: # Linux
            paths_to_check = [
                "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
                "/usr/share/fonts/noto-color-emoji/NotoColorEmoji.ttf",
            ]
            for path in paths_to_check:
                if os.path.exists(path): return path
        return None

    def _load_emoji_font(self, size):
        if not self.EMOJI_FONT_LOADED:
            path = self._get_emoji_font_path()
            if path and os.path.exists(path):
                try:
                    self.EMOJI_FONT = ImageFont.truetype(path, size)
                    print(f"TextOnImage: Loaded emoji font from {path}")
                except Exception as e:
                    print(f"TextOnImage: Warning - Could not load emoji font '{path}': {e}")
                    self.EMOJI_FONT = None
            else:
                print("TextOnImage: Warning - No system emoji font found. Emojis may not render correctly.")
            self.EMOJI_FONT_LOADED = True
        
        if self.EMOJI_FONT and self.EMOJI_FONT.size != size:
             self.EMOJI_FONT = self.EMOJI_FONT.font_variant(size=size)

        return self.EMOJI_FONT

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
                        if f.lower().endswith('.ttf'): font_files.add(f)
            except: pass
        return {"required": {
            "image": ("IMAGE", {"tooltip": "The image or image batch to draw on."}),
            "text": ("STRING", {"forceInput": True, "tooltip": "The text string or batch of strings to draw. Emojis are supported!"}),
            "font_name": (sorted(list(font_files)), {"tooltip": "The font file to use for regular text."}),
            "font_size": ("INT", {"default": 50, "min": 1, "max": 1024, "step": 1, "tooltip": "Font size in pixels."}),
            "font_color": ("STRING", {"default": "255, 255, 255", "tooltip": "Text color in R, G, B format."}),
            "wrap_width": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 1, "tooltip": "Maximum width in pixels for text wrapping. Set to 0 to disable wrapping."}),
            "line_height_multiplier": ("FLOAT", {"default": 1.2, "min": 0.5, "max": 3.0, "step": 0.1, "round": 0.01, "tooltip": "Multiplier for line spacing."}),
            
            # --- NEW STYLING INPUTS ---
            "style": (["None", "Background Block", "Drop Shadow", "Stroke"], {"default": "None"}),
            "style_color": ("STRING", {"default": "0, 0, 0, 128", "tooltip": "R,G,B,A format for the chosen style."}),
            "bg_padding": ("INT", {"default": 10, "min": 0, "max": 200, "step": 1, "tooltip": "Padding for the Background Block."}),
            "shadow_offset": ("INT", {"default": 5, "min": -100, "max": 100, "step": 1, "tooltip": "Offset for the Drop Shadow."}),
            "stroke_width": ("INT", {"default": 2, "min": 0, "max": 50, "step": 1, "tooltip": "Width of the text stroke."}),

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

    def _parse_color(self, color_string, default_color):
        try:
            parts = [int(c.strip()) for c in color_string.split(',')]
            if len(parts) == 3: parts.append(255) # Add full alpha if missing for styles
            return tuple(parts)
        except:
            return default_color

    def _get_text_size(self, draw, text, main_font, emoji_font):
        if emoji_font is None:
            return draw.textbbox((0,0), text, font=main_font)
        
        total_width = 0; min_y = float('inf'); max_y = float('-inf')
        parts = self.EMOJI_SPLIT_REGEX.split(text)
        for part in parts:
            if not part: continue
            font = emoji_font if self.EMOJI_SPLIT_REGEX.match(part) else main_font
            try:
                bbox = draw.textbbox((0,0), part, font=font)
                total_width += bbox[2] - bbox[0]
                min_y = min(min_y, bbox[1])
                max_y = max(max_y, bbox[3])
            except TypeError: pass
        max_height = max_y - min_y if min_y != float('inf') else 0
        return (0, 0, total_width, max_height)

    def _wrap_text(self, text: str, main_font: ImageFont.FreeTypeFont, emoji_font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> str:
        lines = []
        words = text.split(' ')
        if not words: return ""
        current_line = words[0]
        for word in words[1:]:
            test_line = f"{current_line} {word}"
            line_width = self._get_text_size(draw, test_line, main_font, emoji_font)[2]
            if line_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line); current_line = word
        lines.append(current_line)
        return "\n".join(lines)
    
    def _draw_text_chunked(self, draw, pos, text, main_font, emoji_font, fill, **kwargs):
        """Helper to draw a line of mixed text/emoji content."""
        x, y = pos
        parts = self.EMOJI_SPLIT_REGEX.split(text)
        for part in parts:
            if not part: continue
            is_emoji = self.EMOJI_SPLIT_REGEX.match(part)
            font_to_use = emoji_font if is_emoji and emoji_font else main_font
            
            # Pass stroke arguments if they exist
            stroke_width = kwargs.get('stroke_width', 0)
            stroke_fill = kwargs.get('stroke_fill', None)
            
            draw.text((x, y), part, font=font_to_use, fill=fill, embedded_color=True, stroke_width=stroke_width, stroke_fill=stroke_fill)
            part_width = self._get_text_size(draw, part, main_font, emoji_font)[2]
            x += part_width

    def draw_text(self, image, text, font_name, font_size, font_color, wrap_width, line_height_multiplier, style, style_color, bg_padding, shadow_offset, stroke_width, x_position, y_position, horizontal_align, vertical_align, margin):
        num_images = image.shape[0]; text_list = [text] if isinstance(text, str) else text; num_texts = len(text_list)
        loop_count = max(num_images, num_texts)
        if num_images > 1 and num_texts > 1: loop_count = min(num_images, num_texts)
        
        font_path = self.find_font(font_name)
        try: main_font = ImageFont.truetype(font_path, font_size)
        except IOError: main_font = ImageFont.load_default()
        
        main_color_tuple = self._parse_color(font_color, (255, 255, 255))
        style_color_tuple = self._parse_color(style_color, (0, 0, 0, 255))
        
        emoji_font = self._load_emoji_font(font_size)

        output_images = []
        for i in range(loop_count):
            img_tensor = image[i % num_images]
            text_to_draw = text_list[i % num_texts] if text_list else ""
            
            pil_image = Image.fromarray((img_tensor.cpu().numpy() * 255).astype(np.uint8)).convert("RGBA")
            draw = ImageDraw.Draw(pil_image)
            
            final_text = self._wrap_text(text_to_draw, main_font, emoji_font, wrap_width, draw) if wrap_width > 0 else text_to_draw
            
            img_width, img_height = pil_image.size
            lines = final_text.split('\n')
            
            single_line_height = self._get_text_size(draw, "hg", main_font, emoji_font)[3]
            adjusted_line_height = single_line_height * line_height_multiplier

            total_block_width = 0
            for line in lines:
                total_block_width = max(total_block_width, self._get_text_size(draw, line, main_font, emoji_font)[2])
            total_block_height = adjusted_line_height * (len(lines) -1) + single_line_height if lines else 0

            if vertical_align == "top": y_start = margin
            elif vertical_align == "bottom": y_start = img_height - total_block_height - margin
            else: y_start = (img_height - total_block_height) / 2
            y_start += y_position
            
            current_y = y_start
            for line in lines:
                line_width = self._get_text_size(draw, line, main_font, emoji_font)[2]

                if horizontal_align == "left": x_start = margin
                elif horizontal_align == "right": x_start = img_width - total_block_width - margin
                else: x_start = (img_width - total_block_width) / 2
                x_start += x_position

                # Adjust line position for alignment
                line_x_offset = 0
                if horizontal_align == "center":
                    line_x_offset = (total_block_width - line_width) / 2
                elif horizontal_align == "right":
                    line_x_offset = total_block_width - line_width
                
                line_pos = (x_start + line_x_offset, current_y)
                
                # Draw Styles
                if style == "Background Block":
                    bg_x0 = line_pos[0] - bg_padding
                    bg_y0 = line_pos[1] - bg_padding
                    bg_x1 = line_pos[0] + line_width + bg_padding
                    bg_y1 = line_pos[1] + single_line_height + bg_padding
                    draw.rectangle([bg_x0, bg_y0, bg_x1, bg_y1], fill=style_color_tuple)

                elif style == "Drop Shadow":
                    shadow_pos = (line_pos[0] + shadow_offset, line_pos[1] + shadow_offset)
                    self._draw_text_chunked(draw, shadow_pos, line, main_font, emoji_font, fill=style_color_tuple)

                elif style == "Stroke":
                    self._draw_text_chunked(draw, line_pos, line, main_font, emoji_font, fill=main_color_tuple, stroke_width=stroke_width, stroke_fill=style_color_tuple)

                # Draw Main Text
                if style != "Stroke": # If stroking, the main fill is already done
                    self._draw_text_chunked(draw, line_pos, line, main_font, emoji_font, fill=main_color_tuple)

                current_y += adjusted_line_height
            
            final_image = pil_image.convert("RGB")
            output_images.append(torch.from_numpy(np.array(final_image).astype(np.float32) / 255.0))
            
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
        num_images, h, w, c = image.shape
        counts_list = [repeat_counts] if isinstance(repeat_counts, int) else repeat_counts
        num_counts = len(counts_list)

        if num_images == 0 or num_counts == 0 or not any(c > 0 for c in counts_list):
            return (torch.zeros((1, h if h > 0 else 512, w if w > 0 else 512, c if c > 0 else 3), dtype=image.dtype, device=image.device),)

        loop_count = 1
        if num_images > 1 or num_counts > 1:
            loop_count = max(num_images, num_counts)
        if num_images > 1 and num_counts > 1:
            if num_images != num_counts:
                print(f"ImageBatchRepeater: Warning! Mismatched batch sizes: {num_images} images vs {num_counts} counts. Using shorter length.")
            loop_count = min(num_images, num_counts)

        # --- MEMORY OPTIMIZATION ---
        # 1. Pre-calculate the total number of frames to allocate memory only once.
        total_frames = sum(counts_list[i % num_counts] for i in range(loop_count))
        if total_frames <= 0:
            return (torch.zeros((1, h, w, c), dtype=image.dtype, device=image.device),)
        
        print(f"ImageBatchRepeater: Allocating memory for a single {total_frames}-frame timeline.")

        # 2. Pre-allocate the final tensor on the correct device.
        final_timeline = torch.empty((total_frames, h, w, c), dtype=image.dtype, device=image.device)
        
        # 3. Fill the pre-allocated tensor slice by slice.
        current_frame_index = 0
        for i in range(loop_count):
            current_image_tensor = image[i % num_images]
            current_count = counts_list[i % num_counts]
            
            if current_count <= 0:
                continue

            end_frame_index = current_frame_index + current_count
            # Assign the single image tensor to the slice of the final timeline.
            # PyTorch broadcasting handles the repetition efficiently.
            final_timeline[current_frame_index:end_frame_index] = current_image_tensor.unsqueeze(0)
            current_frame_index = end_frame_index
        
        return (final_timeline,)


class MaskBatchRepeater:
    CATEGORY = "Automation/Video"; RETURN_TYPES = ("MASK",); RETURN_NAMES = ("mask_timeline",); FUNCTION = "repeat_batch"
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "mask": ("MASK", {}), "repeat_counts": ("INT", {"forceInput": True}), }}

    def repeat_batch(self, mask, repeat_counts):
        num_masks, h, w = mask.shape
        counts_list = [repeat_counts] if isinstance(repeat_counts, int) else repeat_counts
        num_counts = len(counts_list)

        if num_masks == 0 or num_counts == 0 or not any(c > 0 for c in counts_list):
            return (torch.zeros((1, h if h > 0 else 64, w if w > 0 else 64), dtype=mask.dtype, device=mask.device),)

        loop_count = 1
        if num_masks > 1 or num_counts > 1:
            loop_count = max(num_masks, num_counts)
        if num_masks > 1 and num_counts > 1:
            if num_masks != num_counts:
                print(f"MaskBatchRepeater: Warning! Mismatched batch sizes: {num_masks} masks vs {num_counts} counts. Using shorter length.")
            loop_count = min(num_masks, num_counts)

        # --- MEMORY OPTIMIZATION (Identical logic to ImageBatchRepeater) ---
        total_frames = sum(counts_list[i % num_counts] for i in range(loop_count))
        if total_frames <= 0:
            return (torch.zeros((1, h, w), dtype=mask.dtype, device=mask.device),)
            
        print(f"MaskBatchRepeater: Allocating memory for a single {total_frames}-frame mask timeline.")
            
        final_timeline = torch.empty((total_frames, h, w), dtype=mask.dtype, device=mask.device)
        
        current_frame_index = 0
        for i in range(loop_count):
            current_mask_tensor = mask[i % num_masks]
            current_count = counts_list[i % num_counts]

            if current_count <= 0:
                continue
            
            end_frame_index = current_frame_index + current_count
            final_timeline[current_frame_index:end_frame_index] = current_mask_tensor.unsqueeze(0)
            current_frame_index = end_frame_index

        return (final_timeline,)

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
    
    
# FILE: nodes.py

# ... (previous code, including TextOnImage) ...

class AnimateTextOnImage:
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "animate_text"

    # Emoji logic from before remains the same
    EMOJI_FONT = None
    EMOJI_FONT_LOADED = False
    EMOJI_SPLIT_REGEX = re.compile(
        r'('
        r'['
        '\U0001F1E0-\U0001F1FF' '\U0001F300-\U0001F5FF' '\U0001F600-\U0001F64F'
        '\U0001F680-\U0001F6FF' '\U0001F700-\U0001F77F' '\U0001F780-\U0001F7FF'
        '\U0001F800-\U0001F8FF' '\U0001F900-\U0001F9FF' '\U0001FA00-\U0001FA6F'
        '\U0001FA70-\U0001FAFF' '\U00002702-\U000027B0' '\U000024C2-\U0001F251'
        ']' r')'
    )

    def _get_emoji_font_path(self):
        system = platform.system()
        if system == "Windows": return os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'seguiemj.ttf')
        elif system == "Darwin":
            path = "/System/Library/Fonts/Apple Color Emoji.ttc"
            return path if os.path.exists(path) else "/System/Library/Fonts/Core/AppleColorEmoji.ttf"
        else: # Linux
            for path in ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", "/usr/share/fonts/noto-color-emoji/NotoColorEmoji.ttf"]:
                if os.path.exists(path): return path
        return None

    def _load_emoji_font(self, size):
        if not self.EMOJI_FONT_LOADED:
            path = self._get_emoji_font_path()
            if path and os.path.exists(path):
                try:
                    self.EMOJI_FONT = ImageFont.truetype(path, size)
                    print(f"AnimateTextOnImage: Loaded emoji font from {path}")
                except Exception as e:
                    print(f"AnimateTextOnImage: Warning - Could not load emoji font '{path}': {e}")
            else:
                print("AnimateTextOnImage: Warning - No system emoji font found.")
            self.EMOJI_FONT_LOADED = True
        
        if self.EMOJI_FONT and self.EMOJI_FONT.size != size:
             self.EMOJI_FONT = self.EMOJI_FONT.font_variant(size=size)
        return self.EMOJI_FONT
    
    @classmethod
    def INPUT_TYPES(s):
        # This method is already correct from the previous update, no changes needed here.
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
                "text": ("STRING", {"multiline": True, "forceInput": True, "tooltip": "A single text block or a list of texts to animate in sequence. Emojis are supported!"}),
                "animation_type": (["Typewriter (Character by Character)", "Reveal (Word by Word)"],),
                "animation_duration": ("INT", {"default": 30, "min": 1, "max": 9999, "tooltip": "Duration of the typing/reveal effect for each text block."}),
                "duration_unit": (["Frames", "Percent of Text Duration"], {"default": "Frames", "tooltip": "'Frames': Fixed duration. 'Percent': Duration is a percentage of the text's total display time."}),
                "font_name": (sorted(list(font_files)),),
                "font_size": ("INT", {"default": 50, "min": 1, "max": 1024, "step": 1}),
                "font_color": ("STRING", {"default": "255, 255, 255, 255", "tooltip": "R,G,B,A format for the main text."}),
                "wrap_width": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 1}),
                "line_height_multiplier": ("FLOAT", {"default": 1.2, "min": 0.5, "max": 3.0, "step": 0.1, "round": 0.01}),
                "style": (["None", "Background Block", "Drop Shadow", "Stroke"], {"default": "None"}),
                "style_color": ("STRING", {"default": "0, 0, 0, 128", "tooltip": "R,G,B,A format for the chosen style (background, shadow, or stroke color)."}),
                "bg_padding": ("INT", {"default": 10, "min": 0, "max": 200, "step": 1, "tooltip": "Padding for the Background Block."}),
                "shadow_offset": ("INT", {"default": 5, "min": -100, "max": 100, "step": 1, "tooltip": "Offset for the Drop Shadow."}),
                "stroke_width": ("INT", {"default": 2, "min": 0, "max": 50, "step": 1, "tooltip": "Width of the text stroke."}),
                "x_position": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "y_position": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "horizontal_align": (["left", "center", "right"],),
                "vertical_align": (["top", "center", "bottom"],),
                "margin": ("INT", {"default": 20, "min": 0, "max": 1024, "step": 1})
            },
            "optional": { "text_durations": ("INT", {"forceInput": True}) }
        }

    # Helper methods from before remain the same
    def find_font(self, font_name):
        font_dirs = [];
        if os.name == 'nt': font_dirs.append(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'))
        elif os.name == 'posix': font_dirs.extend(['/usr/share/fonts/truetype/', '/usr/local/share/fonts/', '~/.fonts/', '/System/Library/Fonts/', '/Library/Fonts/'])
        for directory in font_dirs:
            font_path = os.path.join(os.path.expanduser(directory), font_name)
            if os.path.exists(font_path): return font_path
        print(f"ComfyUI_Automation: Font '{font_name}' not found. Falling back to default."); return "DejaVuSans.ttf"

    def _get_text_size(self, draw, text, main_font, emoji_font):
        if emoji_font is None:
            try: bbox = draw.textbbox((0,0), text, font=main_font); return bbox[2] - bbox[0], bbox[3] - bbox[1]
            except TypeError: return 0, 0
        total_width = 0; min_y, max_y = float('inf'), float('-inf')
        for part in self.EMOJI_SPLIT_REGEX.split(text):
            if not part: continue
            font = emoji_font if self.EMOJI_SPLIT_REGEX.match(part) else main_font
            try:
                bbox = draw.textbbox((0,0), part, font=font); total_width += bbox[2] - bbox[0]; min_y, max_y = min(min_y, bbox[1]), max(max_y, bbox[3])
            except TypeError: pass
        max_height = max_y - min_y if min_y != float('inf') else 0; return total_width, max_height

    def _wrap_text(self, text: str, main_font, emoji_font, max_width: int, draw) -> str:
        lines, words = [], text.split(' ')
        if not words: return ""
        current_line = words[0]
        for word in words[1:]:
            test_line = f"{current_line} {word}"
            line_width, _ = self._get_text_size(draw, test_line, main_font, emoji_font)
            if line_width <= max_width: current_line = test_line
            else: lines.append(current_line); current_line = word
        lines.append(current_line); return "\n".join(lines)
    
    def _draw_text_chunked(self, draw, pos, text, main_font, emoji_font, fill, **kwargs):
        x, y = pos
        for part in self.EMOJI_SPLIT_REGEX.split(text):
            if not part: continue
            font_to_use = emoji_font if self.EMOJI_SPLIT_REGEX.match(part) and emoji_font else main_font
            stroke_width, stroke_fill = kwargs.get('stroke_width', 0), kwargs.get('stroke_fill', None)
            draw.text((x, y), part, font=font_to_use, fill=fill, embedded_color=True, stroke_width=stroke_width, stroke_fill=stroke_fill)
            part_width, _ = self._get_text_size(draw, part, main_font, emoji_font)
            x += part_width
    
    def _parse_color(self, color_string, default_color):
        try:
            parts = [int(c.strip()) for c in color_string.split(',')]; parts.append(255) if len(parts) == 3 else None; return tuple(parts)
        except: return default_color



    def animate_text(self, background_image, text, animation_type, animation_duration, duration_unit, font_name, font_size, font_color, wrap_width, line_height_multiplier, style, style_color, bg_padding, shadow_offset, stroke_width, x_position, y_position, horizontal_align, vertical_align, margin, text_durations=None):
        
        output_tensor = background_image
        num_bg_frames = output_tensor.shape[0]

        # All setup and timing calculation logic remains correct
        text_list = [text] if isinstance(text, str) else text
        durations = []
        if text_durations is not None:
            if isinstance(text_durations, list): durations = text_durations
            else:
                try: durations = [int(text_durations)]
                except ValueError: durations = [num_bg_frames]
        else:
            durations = [num_bg_frames] * len(text_list)
        font_path = self.find_font(font_name)
        try: main_font = ImageFont.truetype(font_path, font_size)
        except IOError: main_font = ImageFont.load_default()
        main_color_tuple = self._parse_color(font_color, (255, 255, 255, 255))
        style_color_tuple = self._parse_color(style_color, (0, 0, 0, 128))
        emoji_font = self._load_emoji_font(font_size)
        temp_draw = ImageDraw.Draw(Image.new('RGBA', (1,1)))

        frame_to_text_info = {}
        current_frame = 0
        for i, text_item in enumerate(text_list):
            if i >= len(durations): break
            display_duration = durations[i]
            anim_dur = int(display_duration * (animation_duration / 100.0)) if duration_unit == "Percent of Text Duration" else animation_duration
            anim_dur = max(1, min(anim_dur, display_duration))
            final_text = self._wrap_text(text_item, main_font, emoji_font, wrap_width, temp_draw) if wrap_width > 0 else text_item
            animation_steps = []
            if animation_type == "Typewriter (Character by Character)":
                animation_steps = [final_text[:j+1] for j in range(len(final_text))]
            else:
                unwrapped_words = text_item.split()
                animation_steps = [self._wrap_text(" ".join(unwrapped_words[:j+1]), main_font, emoji_font, wrap_width, temp_draw) if wrap_width > 0 else " ".join(unwrapped_words[:j+1]) for j in range(len(unwrapped_words))]
            num_steps, frames_per_step = len(animation_steps), anim_dur / len(animation_steps) if len(animation_steps) > 0 else float('inf')
            for frame_offset in range(display_duration):
                frame_idx = current_frame + frame_offset
                if frame_idx >= num_bg_frames: break
                text_to_draw = final_text
                if frame_offset < anim_dur and num_steps > 0:
                    text_to_draw = animation_steps[min(int(frame_offset / frames_per_step), num_steps - 1)]
                frame_to_text_info[frame_idx] = {"full_text_layout": final_text, "draw_text": text_to_draw}
            current_frame += display_duration

        # Main Drawing Loop
        canvas_w, canvas_h = output_tensor.shape[2], output_tensor.shape[1]
        for i in range(num_bg_frames):
            text_info = frame_to_text_info.get(i)
            if not (text_info and text_info["draw_text"]): continue

            bg_tensor_frame = output_tensor[i]
            bg_pil = Image.fromarray((bg_tensor_frame.cpu().numpy() * 255).astype(np.uint8)).convert("RGBA")
            text_layer = Image.new('RGBA', bg_pil.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_layer)

            full_text_layout, current_text = text_info["full_text_layout"], text_info["draw_text"]
            full_width, _ = self._get_text_size(temp_draw, full_text_layout, main_font, emoji_font)
            lines_full, (_, single_line_height) = full_text_layout.split('\n'), self._get_text_size(temp_draw, "hg", main_font, emoji_font)
            adjusted_line_height = single_line_height * line_height_multiplier
            total_block_height = adjusted_line_height * (len(lines_full) - 1) + single_line_height if lines_full else 0
            
            if vertical_align == "top": y_start = margin
            elif vertical_align == "bottom": y_start = canvas_h - total_block_height - margin
            else: y_start = (canvas_h - total_block_height) / 2
            if horizontal_align == "left": x_start = margin
            elif horizontal_align == "right": x_start = canvas_w - full_width - margin
            else: x_start = (canvas_w - full_width) / 2
            final_x_base, final_y_base = x_start + x_position, y_start + y_position
            
            lines_to_draw = current_text.split('\n')

            # --- START OF FIX: Final Two-Pass Rendering Logic ---

            # --- PASS 1: Draw background SHAPES only. ---
            if style == "Background Block":
                current_y_bg = final_y_base
                for line in lines_to_draw:
                    line_width, _ = self._get_text_size(temp_draw, line, main_font, emoji_font)
                    line_x_offset = (full_width - line_width) / 2 if horizontal_align == "center" else (full_width - line_width) if horizontal_align == "right" else 0
                    line_pos = (final_x_base + line_x_offset, current_y_bg)
                    draw.rectangle([line_pos[0] - bg_padding, line_pos[1] - bg_padding, line_pos[0] + line_width + bg_padding, line_pos[1] + single_line_height + bg_padding], fill=style_color_tuple)
                    current_y_bg += adjusted_line_height

            # --- PASS 2: Draw all TEXT-BASED elements in the correct order. ---
            current_y_text = final_y_base
            for line in lines_to_draw:
                line_width, _ = self._get_text_size(temp_draw, line, main_font, emoji_font)
                line_x_offset = (full_width - line_width) / 2 if horizontal_align == "center" else (full_width - line_width) if horizontal_align == "right" else 0
                line_pos = (final_x_base + line_x_offset, current_y_text)

                # A. Draw shadow or stroke layer first.
                if style == "Drop Shadow":
                    shadow_pos = (line_pos[0] + shadow_offset, line_pos[1] + shadow_offset)
                    self._draw_text_chunked(draw, shadow_pos, line, main_font, emoji_font, fill=style_color_tuple)
                
                elif style == "Stroke":
                    # This draws the "fattened" text to create the outline effect.
                    self._draw_text_chunked(draw, line_pos, line, main_font, emoji_font, fill=style_color_tuple, stroke_width=stroke_width, stroke_fill=style_color_tuple)
                
                # B. ALWAYS draw the main, solid text fill ON TOP of any effect.
                self._draw_text_chunked(draw, line_pos, line, main_font, emoji_font, fill=main_color_tuple)
                
                current_y_text += adjusted_line_height

            # --- END OF FIX ---
            
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
                "interpolation": (resampling_methods, {"default": "LANCZOS", "tooltip": "The resampling filter to use for resizing. LANCZOS is high quality."}),
            }
        }

    def _tensor_to_pil(self, tensor, is_mask=False):
        if tensor is None: return None
        image_tensor = tensor[0] 
        if is_mask:
            image_tensor = image_tensor.unsqueeze(-1)
        np_array = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
        if np_array.shape[-1] == 1:
            np_array = np_array.squeeze(-1)
        return Image.fromarray(np_array)

    def _pil_to_tensor(self, pil_image):
        return torch.from_numpy(np.array(pil_image).astype(np.float32) / 255.0).unsqueeze(0)

    def process(self, background_image, overlay_image, overlay_mask, size, rotation, x_offset, y_offset, interpolation):
        bg_pil = self._tensor_to_pil(background_image)
        overlay_pil = self._tensor_to_pil(overlay_image)
        mask_pil = self._tensor_to_pil(overlay_mask, is_mask=True)

        if bg_pil is None or overlay_pil is None or mask_pil is None:
            return (torch.zeros((1, 64, 64, 3)),)

        resampling_filter = getattr(Image.Resampling, interpolation, Image.Resampling.LANCZOS)

        overlay_rgba = overlay_pil.convert("RGBA")
        overlay_rgba.putalpha(mask_pil)

        # 1. Scale the overlay using the user-selected filter
        if overlay_rgba.width > 0 and overlay_rgba.height > 0:
            aspect_ratio = overlay_rgba.width / overlay_rgba.height
            if overlay_rgba.width >= overlay_rgba.height:
                new_w, new_h = size, max(1, int(size / aspect_ratio))
            else:
                new_h, new_w = size, max(1, int(size * aspect_ratio))
            overlay_rgba = overlay_rgba.resize((new_w, new_h), resample=resampling_filter)

        # 2. Rotate the scaled overlay
        if rotation != 0:
            # --- START OF FIX ---
            # Use a high-quality filter that is supported by .rotate()
            rotation_filter = Image.Resampling.BICUBIC
            overlay_rgba = overlay_rgba.rotate(rotation, resample=rotation_filter, expand=True)
            # --- END OF FIX ---
            
        # 3. Paste onto the background
        bg_rgba = bg_pil.convert("RGBA")
        
        canvas_center_x, canvas_center_y = bg_rgba.width // 2, bg_rgba.height // 2
        paste_x = canvas_center_x + x_offset - (overlay_rgba.width // 2)
        paste_y = canvas_center_y + y_offset - (overlay_rgba.height // 2)

        bg_rgba.paste(overlay_rgba, (paste_x, paste_y), mask=overlay_rgba)

        final_pil = bg_rgba.convert("RGB")
        output_tensor = self._pil_to_tensor(final_pil)

        return (output_tensor,)
    
class GaussianBlur:
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply_blur"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "The image or image batch to apply the blur to."}),
                "radius": ("FLOAT", {"default": 10.0, "min": 0.0, "max": 500.0, "step": 0.1, "round": 0.01, "tooltip": "The radius of the Gaussian blur. Higher values create a stronger blur effect."}),
            }
        }
    
    def _tensor_to_pil(self, tensor_frame):
        return Image.fromarray((tensor_frame.cpu().numpy() * 255).astype(np.uint8))

    def _pil_to_tensor(self, pil_image):
        return torch.from_numpy(np.array(pil_image).astype(np.float32) / 255.0)

    def apply_blur(self, image, radius):
        # If radius is zero or negative, no blur is needed. Return original image.
        if radius <= 0:
            return (image,)
            
        # This list will hold the processed (blurred) frames.
        blurred_frames = []
        
        # Iterate over each image in the batch.
        for i in range(image.shape[0]):
            # Convert the current frame (tensor) to a PIL Image.
            pil_image = self._tensor_to_pil(image[i])
            
            # Apply the Gaussian Blur filter.
            blurred_image = pil_image.filter(ImageFilter.GaussianBlur(radius=radius))
            
            # Convert the blurred PIL Image back to a tensor.
            blurred_tensor_frame = self._pil_to_tensor(blurred_image)
            
            # Add the processed frame to our list.
            blurred_frames.append(blurred_tensor_frame)
        
        # Stack the list of processed frames back into a single batch tensor.
        output_image = torch.stack(blurred_frames)
        
        return (output_image,)
    
class WebhookUploader:
    CATEGORY = "Automation/Publishing"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response_text",)
    FUNCTION = "send_webhook"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "webhook_url": ("STRING", {"multiline": False, "tooltip": "The unique webhook URL from your automation service (e.g., Make.com, Zapier)."}),
                "video_url": ("STRING", {"forceInput": True, "tooltip": "The public URL of the video to be posted (e.g., from an S3 Uploader node)."}),
                "description": ("STRING", {"multiline": True, "default": "", "tooltip": "The description/caption for the video."}),
            },
            "optional": {
                "thumbnail_url": ("STRING", {"forceInput": True, "tooltip": "Optional: The public URL of the thumbnail image."}),
                "any_string_1": ("STRING", {"multiline": False, "default": "", "tooltip": "An extra text field you can use in your automation."}),
                "any_string_2": ("STRING", {"multiline": False, "default": "", "tooltip": "Another extra text field."}),
            }
        }

    def send_webhook(self, webhook_url, video_url, description, thumbnail_url="", any_string_1="", any_string_2=""):
        if not webhook_url:
            return ("Webhook URL is empty. Skipping.",)
        
        # Prepare the JSON data payload
        payload = {
            'video_url': video_url,
            'thumbnail_url': thumbnail_url,
            'description': description,
            'any_string_1': any_string_1,
            'any_string_2': any_string_2
        }
        
        headers = {
            'Content-Type': 'application/json'
        }

        try:
            print(f"WebhookUploader: Sending JSON payload to {webhook_url}")
            response = requests.post(webhook_url, json=payload, headers=headers)
            response_text = f"Status Code: {response.status_code}\nResponse: {response.text}"
            print(f"WebhookUploader: {response_text}")
            return (response_text,)

        except Exception as e:
            error_message = f"WebhookUploader: FAILED to send request. Error: {e}"
            print(error_message)
            traceback.print_exc()
            return (error_message,)

class S3Uploader:
    CATEGORY = "Automation/Publishing"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("public_url",)
    FUNCTION = "upload_to_s3"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "file_path": ("STRING", {"forceInput": True, "tooltip": "The local path of the file (video, image, etc.) to upload."}),
                "bucket_name": ("STRING", {"multiline": False, "tooltip": "The name of your Amazon S3 bucket."}),
                "aws_access_key_id": ("STRING", {"multiline": False, "tooltip": "Your AWS Access Key ID."}),
                "aws_secret_access_key": ("STRING", {"multiline": False, "tooltip": "Your AWS Secret Access Key. Treat this like a password."}),
                "aws_region": ("STRING", {"multiline": False, "default": "us-east-1", "tooltip": "The AWS region your bucket is in (e.g., 'us-west-2', 'eu-central-1')."}),
            },
            "optional": {
                "object_name": ("STRING", {"multiline": False, "tooltip": "Optional: The desired name for the file in the bucket (including folders, e.g., 'videos/my_vid.mp4'). If empty, the original filename is used."}),
            }
        }

    def upload_to_s3(self, file_path, bucket_name, aws_access_key_id, aws_secret_access_key, aws_region, object_name=None):
        if not all([aws_access_key_id, aws_secret_access_key, bucket_name, aws_region]):
            return ("Error: AWS credentials, region, and bucket name are all required.",)
            
        if not os.path.exists(file_path):
            return (f"Error: File not found at '{file_path}'.",)

        # If object_name is not specified, use the base filename
        if not object_name:
            object_name = os.path.basename(file_path)

        # Create an S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )

        try:
            print(f"S3Uploader: Uploading '{file_path}' to bucket '{bucket_name}' as '{object_name}'...")
            
            # The ACL='public-read' makes the file publicly accessible via its URL.
            s3_client.upload_file(
                file_path, 
                bucket_name, 
                object_name,
                ExtraArgs={'ACL': 'public-read'}
            )
            
            # Construct the public URL
            public_url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{object_name}"
            print(f"S3Uploader: Upload successful. Public URL: {public_url}")
            
            return (public_url,)

        except (NoCredentialsError, PartialCredentialsError):
            return ("Error: AWS credentials not found or incomplete.",)
        except Exception as e:
            error_message = f"S3Uploader: FAILED to upload. Error: {e}"
            print(error_message)
            traceback.print_exc()
            return (error_message,)
        
class TimeScheduler:
    CATEGORY = "Automation/Time"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("formatted_date", "formatted_time")
    FUNCTION = "calculate_time"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mode": (["Offset from Current Time", "Next Specific Time"], {"default": "Offset from Current Time"}),
                "utc_timezone": ("STRING", {"default": "Europe/Berlin", "tooltip": "The target timezone for calculation, e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo'. See pytz documentation for a full list."}),
            },
            "optional": {
                # Inputs for "Offset" mode
                "offset_days": ("INT", {"default": 0, "min": 0, "max": 365}),
                "offset_hours": ("INT", {"default": 0, "min": 0, "max": 23}),
                "offset_minutes": ("INT", {"default": 0, "min": 0, "max": 59}),
                
                # Inputs for "Specific Time" mode
                "specific_time": ("STRING", {"default": "08:30", "tooltip": "The specific time in HH:MM format to schedule for the next day."}),
            }
        }

    def calculate_time(self, mode, utc_timezone, offset_days=0, offset_hours=0, offset_minutes=0, specific_time="08:30"):
        try:
            # Get the target timezone object
            tz = timezone(utc_timezone)
        except Exception as e:
            print(f"TimeScheduler Error: Invalid timezone '{utc_timezone}'. Falling back to UTC. Error: {e}")
            tz = utc

        # Get the current time in the specified timezone
        now_in_tz = datetime.datetime.now(tz)
        print(f"TimeScheduler: Current time in {utc_timezone} is {now_in_tz.strftime('%Y-%m-%d %H:%M:%S')}")

        final_datetime = None

        if mode == "Offset from Current Time":
            # Calculate the offset
            offset = datetime.timedelta(days=offset_days, hours=offset_hours, minutes=offset_minutes)
            final_datetime = now_in_tz + offset
            print(f"TimeScheduler: Applying offset of {offset_days}d {offset_hours}h {offset_minutes}m.")
        
        elif mode == "Next Specific Time":
            try:
                # Parse the target time
                target_hour, target_minute = map(int, specific_time.split(':'))
                
                # Create a datetime object for the target time today
                target_time_today = now_in_tz.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                
                # If that time has already passed today, schedule it for tomorrow
                if now_in_tz > target_time_today:
                    final_datetime = target_time_today + datetime.timedelta(days=1)
                    print(f"TimeScheduler: Target time {specific_time} has passed for today. Scheduling for tomorrow.")
                else:
                    final_datetime = target_time_today
                    print(f"TimeScheduler: Scheduling for target time {specific_time} today.")

            except ValueError:
                print(f"TimeScheduler Error: Invalid 'specific_time' format '{specific_time}'. Must be HH:MM. Using current time.")
                final_datetime = now_in_tz
        
        if final_datetime is None:
             final_datetime = now_in_tz

        # Format the final datetime into the required strings
        formatted_date = final_datetime.strftime("%Y-%m-%d")
        formatted_time = final_datetime.strftime("%H:%M")
        
        print(f"TimeScheduler: Calculated schedule - Date: {formatted_date}, Time: {formatted_time}")

        return (formatted_date, formatted_time)
    
def _format_bytes(byte_size):
    """Helper function to format bytes into KB, MB, GB, etc."""
    if byte_size is None or byte_size < 0:
        return "0 B"
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while byte_size > power and n < len(power_labels) -1 :
        byte_size /= power
        n += 1
    return f"{byte_size:.2f} {power_labels[n]}B"

class MemoryPurge:
    """
    A utility node to force garbage collection and report on freed memory.
    This version is an IMAGE passthrough, designed to be placed on a connection
    that carries an IMAGE batch.
    """
    CATEGORY = "Automation/Utils"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image_passthrough",)
    FUNCTION = "purge"
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
            },
        }

    def purge(self, image):
        print("--- MemoryPurge Node: Starting Cleanup ---")
        
        # --- Measure Before ---
        process = psutil.Process(os.getpid()) if PSUTIL_AVAILABLE else None
        
        ram_before = process.memory_info().rss if process else -1
        vram_before = torch.cuda.memory_allocated() if torch.cuda.is_available() else -1
        
        if process:
             print(f"RAM Usage Before: {_format_bytes(ram_before)}")
        if vram_before != -1:
             print(f"VRAM Usage Before: {_format_bytes(vram_before)}")

        # --- Perform Cleanup ---
        print("Forcing garbage collection and emptying CUDA cache...")
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # --- Measure After ---
        ram_after = process.memory_info().rss if process else -1
        vram_after = torch.cuda.memory_allocated() if torch.cuda.is_available() else -1

        print("--- MemoryPurge Node: Cleanup Report ---")
        if process:
            ram_freed = ram_before - ram_after
            print(f"RAM Usage After:  {_format_bytes(ram_after)} (Freed: {_format_bytes(ram_freed)})")
        else:
            print("RAM Usage: psutil not installed, cannot report.")

        if vram_before != -1:
            vram_freed = vram_before - vram_after
            print(f"VRAM Usage After: {_format_bytes(vram_after)} (Freed: {_format_bytes(vram_freed)})")
        else:
            print("VRAM Usage: No CUDA device detected.")
        print("------------------------------------------")
        
        # Pass through the original image tensor without modification
        return (image,)
    
class GetLastImageFromBatch:
    """
    Selects and outputs the very last image from an input image batch.
    """
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("last_image",)
    FUNCTION = "get_last"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_batch": ("IMAGE", {"tooltip": "The batch of images (e.g., a video timeline) to get the last frame from."}),
            }
        }

    def get_last(self, image_batch):
        # Check if the input batch is valid and has at least one image
        if image_batch is None or image_batch.shape[0] == 0:
            print("GetLastImageFromBatch: Warning - Input image batch is empty. Returning a black image.")
            # Return a default 64x64 black tensor
            return (torch.zeros((1, 64, 64, 3), dtype=torch.float32),)

        # Select the last image tensor from the batch.
        # This removes the batch dimension, resulting in a shape of (height, width, channels).
        last_image = image_batch[-1]
        
        # Add the batch dimension back, so the shape becomes (1, height, width, channels),
        # which is the correct format for a ComfyUI IMAGE output.
        last_image_as_batch = last_image.unsqueeze(0)
        
        print(f"GetLastImageFromBatch: Selected the last image from a batch of {image_batch.shape[0]}.")

        return (last_image_as_batch,)
    
class AnimateGaussianBlur:
    """
    Applies a Gaussian blur to a batch of images with a radius that animates linearly
    from 0 on the first frame to a specified max_radius on the last frame.
    """
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "animate_blur"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "The image batch (video timeline) to apply the animated blur to."}),
                "max_radius": ("FLOAT", {"default": 25.0, "min": 0.0, "max": 500.0, "step": 0.1, "round": 0.01, "tooltip": "The maximum blur strength, reached at the last frame of the batch."}),
            }
        }

    def _tensor_to_pil(self, tensor_frame):
        return Image.fromarray((tensor_frame.cpu().numpy() * 255).astype(np.uint8))

    def _pil_to_tensor(self, pil_image):
        return torch.from_numpy(np.array(pil_image).astype(np.float32) / 255.0)

    def animate_blur(self, image, max_radius):
        # If max_radius is effectively zero, no blur is needed. Return the original image.
        if max_radius <= 0:
            return (image,)

        num_frames = image.shape[0]
        
        # If there's no batch or only one frame, we can't animate.
        # We'll just blur the single frame with the max radius.
        if num_frames <= 1:
            pil_image = self._tensor_to_pil(image[0])
            blurred_image = pil_image.filter(ImageFilter.GaussianBlur(radius=max_radius))
            blurred_tensor = self._pil_to_tensor(blurred_image).unsqueeze(0)
            return (blurred_tensor,)
            
        print(f"AnimateGaussianBlur: Animating blur from 0 to {max_radius} over {num_frames} frames.")
        
        blurred_frames = []
        
        # Iterate over each frame in the batch.
        for i in range(num_frames):
            # Calculate the progress of the animation (from 0.0 to 1.0)
            progress = i / (num_frames - 1)
            
            # Calculate the blur radius for the current frame
            current_radius = max_radius * progress

            # If the radius is negligible, don't waste time blurring.
            if current_radius < 0.01:
                # We still need to add the original frame to maintain the batch.
                blurred_frames.append(image[i])
                continue

            # Convert the current frame (tensor) to a PIL Image.
            pil_image = self._tensor_to_pil(image[i])
            
            # Apply the Gaussian Blur filter with the calculated radius.
            blurred_image = pil_image.filter(ImageFilter.GaussianBlur(radius=current_radius))
            
            # Convert the blurred PIL Image back to a tensor.
            blurred_tensor_frame = self._pil_to_tensor(blurred_image)
            
            # Add the processed frame to our list.
            blurred_frames.append(blurred_tensor_frame)
        
        # Stack the list of processed frames back into a single batch tensor.
        output_image = torch.stack(blurred_frames)
        
        return (output_image,)
    
class ImageBatchConcatenator:
    """
    A memory-efficient node to concatenate multiple image batches into a single batch.
    It has one required input and multiple optional inputs for clarity.
    """
    CATEGORY = "Automation/Utils"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("combined_image_batch",)
    FUNCTION = "concatenate"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_batch_1": ("IMAGE", {"tooltip": "The first image batch. This one is required."}),
            },
            "optional": {
                # Add several optional inputs for user-friendliness
                "image_batch_2": ("IMAGE", {"tooltip": "An optional second image batch."}),
                "image_batch_3": ("IMAGE", {"tooltip": "An optional third image batch."}),
                "image_batch_4": ("IMAGE", {"tooltip": "An optional fourth image batch."}),
                "image_batch_5": ("IMAGE", {"tooltip": "An optional fifth image batch."}),
            }
        }

    def concatenate(self, image_batch_1, image_batch_2=None, image_batch_3=None, image_batch_4=None, image_batch_5=None):
        # 1. --- Gather all provided batches into a list ---
        all_batches = [b for b in [image_batch_1, image_batch_2, image_batch_3, image_batch_4, image_batch_5] if b is not None]

        if not all_batches or not any(b.shape[0] > 0 for b in all_batches):
            print("ImageBatchConcatenator: Warning - No valid image batches provided. Returning a black frame.")
            return (torch.zeros((1, 64, 64, 3)),)

        # 2. --- Validation and Pre-calculation (same logic as before) ---
        first_batch = all_batches[0]
        h, w, c = first_batch.shape[1], first_batch.shape[2], first_batch.shape[3]
        dtype = first_batch.dtype
        device = first_batch.device
        
        total_frames = 0
        print("ImageBatchConcatenator: Validating input batches...")

        for i, batch in enumerate(all_batches):
            if batch.shape[1] != h or batch.shape[2] != w or batch.shape[3] != c:
                print(f"!!! ERROR: ImageBatchConcatenator - Mismatched dimensions detected!")
                print(f"    Batch 1 shape: {h}x{w}x{c}")
                print(f"    Batch {i+1} shape: {batch.shape[1]}x{batch.shape[2]}x{batch.shape[3]}")
                print(f"    Concatenation aborted. Returning the first batch only.")
                return (first_batch,)
            total_frames += batch.shape[0]
        
        print(f"ImageBatchConcatenator: Found {len(all_batches)} valid batches. Total frames to combine: {total_frames}.")

        # 3. --- Memory-Efficient Allocation and Concatenation ---
        try:
            combined_batch = torch.empty((total_frames, h, w, c), dtype=dtype, device=device)
            print(f"ImageBatchConcatenator: Successfully allocated memory for the final {total_frames}-frame timeline.")
        except Exception as e:
            print(f"!!! ERROR: ImageBatchConcatenator - Failed to allocate memory. Your timeline is likely too large for RAM.")
            print(f"    Error details: {e}")
            return (first_batch,)

        current_pos = 0
        for batch in all_batches:
            num_frames_in_batch = batch.shape[0]
            if num_frames_in_batch == 0: continue
            combined_batch[current_pos : current_pos + num_frames_in_batch] = batch
            current_pos += num_frames_in_batch
        
        print("ImageBatchConcatenator: Concatenation complete.")
        return (combined_batch,)
    
class GreenScreenKeyer:
    """
    Generates a mask from a specified key color (e.g., green screen) in a batch of images.
    Provides controls for threshold and softness for fine-tuning the key.
    """
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image_out", "mask")
    FUNCTION = "key_image"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "The image batch to perform the keying on."}),
                "key_color": ("STRING", {"default": "0, 255, 0", "tooltip": "The RGB color to key out (e.g., '0, 255, 0' for pure green)."}),
                "threshold": ("FLOAT", {"default": 0.4, "min": 0.0, "max": 1.732, "step": 0.01, "tooltip": "The tolerance for the key. Higher values include more color variations."}),
                "softness": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "The falloff or feathering of the mask's edge. Creates a smoother transition."}),
                "invert_mask": ("BOOLEAN", {"default": False, "label_on": "Yes", "label_off": "No", "tooltip": "If True, the keyed color will be white in the mask instead of black."}),
            }
        }

    def _parse_color_tensor(self, color_string, device):
        try:
            # Parse R, G, B values from the string and normalize them to 0-1 range
            color = [float(c.strip()) / 255.0 for c in color_string.split(',')]
            if len(color) != 3:
                raise ValueError
            return torch.tensor(color, device=device).view(1, 1, 1, 3)
        except Exception:
            print(f"GreenScreenKeyer: Warning - Invalid key_color '{color_string}'. Defaulting to pure green.")
            return torch.tensor([0.0, 1.0, 0.0], device=device).view(1, 1, 1, 3)

    def key_image(self, image, key_color, threshold, softness, invert_mask):
        # The input `image` is a batch of shape (B, H, W, C)
        
        # Prepare the key color tensor
        key_color_t = self._parse_color_tensor(key_color, image.device)

        # Calculate the difference between each pixel and the key color
        # This uses broadcasting to subtract the (1,1,1,3) key_color from the (B,H,W,3) image
        diff = image - key_color_t
        
        # Calculate the Euclidean distance for each pixel. The result is a (B, H, W) tensor.
        # This measures how "far" each pixel's color is from the target key_color.
        distances = torch.sqrt(torch.sum(diff ** 2, dim=3))

        # Normalize the mask based on threshold and softness
        # Anything with a distance below (threshold - softness) will be 0.
        # Anything with a distance above threshold will be 1.
        # Anything in between will be a smooth gradient.
        softness = max(0.001, softness) # Avoid division by zero
        
        # Calculate the mask by scaling the distances within the softness range
        mask = (distances - (threshold - softness)) / softness
        
        # Clamp the values to the 0-1 range to create a valid mask
        mask = torch.clamp(mask, 0, 1)

        # Invert the mask if requested
        if invert_mask:
            mask = 1.0 - mask
        
        print(f"GreenScreenKeyer: Successfully generated mask for a batch of {image.shape[0]} images.")

        # Return the original image (as a passthrough) and the generated mask batch
        return (image, mask)
    
class TransformPasterBatch:
    """
    A memory-efficient node to transform and paste an overlay batch onto a background batch.
    It processes frame-by-frame with options for start offset and alignment.
    """
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("composited_image",)
    FUNCTION = "process_batch"

    @classmethod
    def INPUT_TYPES(s):
        resampling_methods = ["LANCZOS", "BICUBIC", "BILINEAR", "NEAREST"]
        
        return {
            "required": {
                "background_image": ("IMAGE", {"tooltip": "The base video timeline to paste onto."}),
                "overlay_image": ("IMAGE", {"tooltip": "The overlay video timeline to transform and paste."}),
                "overlay_mask": ("MASK", {"tooltip": "The mask or mask timeline for the overlay."}),
                
                # --- NEW CONTROL INPUTS ---
                "alignment_mode": (["Paste at Start", "Paste at End"], {"default": "Paste at Start", "tooltip": "Align the overlay relative to the start or the end of the background timeline."}),
                "start_frame_offset": ("INT", {"default": 0, "min": -99999, "max": 99999, "step": 1, "tooltip": "Offset in frames from the chosen alignment point. For 'Paste at End', a positive value moves it earlier."}),

                "size": ("INT", {"default": 256, "min": 1, "max": 8192, "step": 8}),
                "rotation": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0, "step": 0.1, "round": 0.01}),
                "x_offset": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "y_offset": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "interpolation": (resampling_methods, {"default": "LANCZOS"}),
            }
        }

    def _tensor_to_pil(self, tensor_frame, is_mask=False):
        if tensor_frame is None: return None
        np_array = (tensor_frame.cpu().numpy() * 255).astype(np.uint8)
        return Image.fromarray(np_array, 'L') if is_mask else Image.fromarray(np_array, 'RGB')

    def _pil_to_tensor(self, pil_image):
        return torch.from_numpy(np.array(pil_image).astype(np.float32) / 255.0)

    def process_batch(self, background_image, overlay_image, overlay_mask, alignment_mode, start_frame_offset, size, rotation, x_offset, y_offset, interpolation):
        
        num_bg_frames = background_image.shape[0]
        num_overlay_frames = overlay_image.shape[0]
        num_mask_frames = overlay_mask.shape[0]

        # Work in-place on the background image tensor to save memory
        output_timeline = background_image
        
        # --- START OF NEW LOGIC: Calculate the paste window ---
        paste_start_index = 0
        if alignment_mode == "Paste at End":
            # Calculate the start frame so the overlay's last frame aligns with the background's last frame.
            # Then, subtract the offset (a positive offset moves it earlier in time).
            paste_start_index = (num_bg_frames - num_overlay_frames) - start_frame_offset
        else: # "Paste at Start"
            paste_start_index = start_frame_offset
            
        paste_end_index = paste_start_index + num_overlay_frames
        
        print(f"TransformPasterBatch: Alignment='{alignment_mode}', Offset={start_frame_offset}.")
        print(f"TransformPasterBatch: Calculated paste window for background: frames {paste_start_index} to {paste_end_index - 1}.")
        # --- END OF NEW LOGIC ---

        resampling_filter = getattr(Image.Resampling, interpolation, Image.Resampling.LANCZOS)

        # Loop through all background frames
        for i in range(num_bg_frames):
            
            # Check if the current frame is inside our calculated paste window.
            if i >= paste_start_index and i < paste_end_index:
                # Calculate the corresponding index for the overlay and mask.
                overlay_idx = i - paste_start_index
                mask_idx = overlay_idx % num_mask_frames
                
                # 1. Convert single frames to PIL
                bg_pil = self._tensor_to_pil(output_timeline[i]).convert("RGBA")
                overlay_pil = self._tensor_to_pil(overlay_image[overlay_idx])
                mask_pil = self._tensor_to_pil(overlay_mask[mask_idx], is_mask=True)
                
                overlay_rgba = overlay_pil.convert("RGBA")
                overlay_rgba.putalpha(mask_pil)

                # 2. Scale
                if overlay_rgba.width > 0 and overlay_rgba.height > 0:
                    aspect = overlay_rgba.width / overlay_rgba.height
                    new_w, new_h = (size, max(1, int(size / aspect))) if aspect >= 1 else (max(1, int(size * aspect)), size)
                    overlay_rgba = overlay_rgba.resize((new_w, new_h), resample=resampling_filter)

                # 3. Rotate
                if rotation != 0:
                    overlay_rgba = overlay_rgba.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)
                
                # 4. Paste
                paste_x = (bg_pil.width // 2) + x_offset - (overlay_rgba.width // 2)
                paste_y = (bg_pil.height // 2) + y_offset - (overlay_rgba.height // 2)
                bg_pil.paste(overlay_rgba, (paste_x, paste_y), mask=overlay_rgba)

                # 5. Convert back to tensor and update timeline
                output_timeline[i] = self._pil_to_tensor(bg_pil.convert("RGB"))
            else:
                # If we're outside the paste window, do nothing.
                continue

        print("TransformPasterBatch: Processing complete.")
        return (output_timeline,)