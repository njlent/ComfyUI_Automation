import feedparser
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image, ImageOps
import numpy as np
import torch
import io

# --- RSS FEEDER NODE ---
class RssFeedReader:
    CATEGORY = "Automation/RSS"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("raw_output", "formatted_text", "content_batch_1", "content_batch_2")
    FUNCTION = "read_feed"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "links": ("STRING", {"multiline": True, "default": "", "tooltip": "One or more RSS feed URLs, each on a new line."}),
                "max_entries": ("INT", {"default": 3, "min": 1, "max": 100, "step": 1, "tooltip": "The maximum number of entries to fetch from EACH feed in the list."}),
                "skip_entries": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1, "tooltip": "Skips the first N entries from each feed. Useful for pagination."}),
                "batch_source_1": (["title", "summary", "link"], {"default": "title", "tooltip": "Select the content (title, summary, or link) for the first batch output."}),
                "batch_source_2": (["title", "summary", "link"], {"default": "summary", "tooltip": "Select the content (title, summary, or link) for the second batch output."}),
                "output_mode": (["Concatenated String", "Batch Output"], {"default": "Concatenated String", "tooltip": "Controls how raw_output and formatted_text are returned. 'Batch Output' creates synchronized lists."}),
            }
        }

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
    def INPUT_TYPES(s):
        return {
            "required": {
                "url": ("STRING", {"multiline": False, "default": "", "tooltip": "A single URL or a batch of URLs (from another node) to scrape."}),
            }
        }
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
                    if src := i.get('src'):
                        if (a_url := self._abs(s, src)) not in au: au.append(a_url)
            except Exception as e: print(f"ComfyUI_Automation: Scraper Error: {e}")
        return (at, au)

class TargetedWebScraper:
    CATEGORY = "Automation/Web"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("extracted_text", "image_urls")
    FUNCTION = "scrape_targeted"
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "url": ("STRING", {"multiline": False, "default": "", "tooltip": "A single URL or a batch of URLs (from another node) to scrape."}),
                "selectors": ("STRING", {"multiline": True, "default": "body", "tooltip": "CSS selectors for the content you WANT to extract (e.g., .article-body, h1). Use browser's 'Inspect Element' tool to find them."}),
                "ignore_selectors": ("STRING", {"multiline": True, "default": "nav, footer, .ad-container", "tooltip": "CSS selectors for content to REMOVE before extraction (e.g., nav, footer, .ads). This cleans the page first."}),
            }
        }
    def _make_absolute_url(self, b, l): return urljoin(b, l)
    def scrape_targeted(self, url, selectors, ignore_selectors):
        url_list = [url] if isinstance(url, str) else url
        final_text_batch, final_image_batch = [], []
        selector_list = [s.strip() for s in selectors.splitlines() if s.strip()]
        ignore_selector_list = [s.strip() for s in ignore_selectors.splitlines() if s.strip()]
        if not selector_list: return ([], [])
        for single_url in url_list:
            if not single_url: continue
            try:
                response = requests.get(single_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10); response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                if ignore_selector_list:
                    for ignored in soup.select(','.join(ignore_selector_list)): ignored.decompose()
                for element in soup.select(','.join(selector_list)):
                    if text := element.get_text(separator=' ', strip=True): final_text_batch.append(text)
                    for img in element.find_all('img'):
                        if src := img.get('src'):
                            abs_url = self._make_absolute_url(single_url, src)
                            if abs_url not in final_image_batch: final_image_batch.append(abs_url)
            except Exception as e: print(f"ComfyUI_Automation: Targeted Scraper Error on {single_url}: {e}")
        return (final_text_batch, final_image_batch)

# --- IMAGE LOADER NODE ---
class LoadImageFromURL:
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image_from_url"
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "A single image URL or a batch of URLs to download."}),
                "resize_mode": (["Don't Resize (First Image Only)", "Stretch", "Crop (Center)", "Pad (Black)"], {"default": "Pad (Black)", "tooltip": "How to handle images of different sizes. 'Don't Resize' is not batch-compatible."}),
                "target_width": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8, "tooltip": "The width all images will be resized to (unless 'Don't Resize' is selected)."}),
                "target_height": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8, "tooltip": "The height all images will be resized to (unless 'Don't Resize' is selected)."}),
            }
        }
    def load_image_from_url(self, image_url, resize_mode, target_width, target_height):
        url_list = [image_url] if isinstance(image_url, str) else image_url
        image_tensors, mask_tensors = [], []
        headers = {'User-Agent': 'Mozilla/5.0'}
        target_size = (target_width, target_height)
        for url in url_list:
            if not url or not url.strip().startswith(('http://', 'https://')): continue
            try:
                response = requests.get(url, headers=headers, timeout=20); response.raise_for_status()
                i = Image.open(io.BytesIO(response.content)); original_mode = i.mode
                if resize_mode == "Stretch": i = i.resize(target_size, Image.Resampling.LANCZOS)
                elif resize_mode == "Crop (Center)": i = ImageOps.fit(i, target_size, Image.Resampling.LANCZOS)
                elif resize_mode == "Pad (Black)":
                    img_copy = i.copy(); img_copy.thumbnail(target_size, Image.Resampling.LANCZOS)
                    background = Image.new('RGB', target_size, (0, 0, 0))
                    paste_pos = ((target_size[0] - img_copy.width) // 2, (target_size[1] - img_copy.height) // 2)
                    background.paste(img_copy, paste_pos); i = background
                i = i.convert("RGB"); image = np.array(i).astype(np.float32) / 255.0
                image_tensors.append(torch.from_numpy(image)[None,])
                if original_mode == 'RGBA':
                    mask = np.array(Image.open(io.BytesIO(response.content)).getchannel('A')).astype(np.float32) / 255.0
                    if resize_mode != "Don't Resize (First Image Only)":
                         mask_img = Image.fromarray(mask); mask_img = mask_img.resize(target_size, Image.Resampling.LANCZOS)
                         mask = np.array(mask_img)
                    mask_tensors.append(torch.from_numpy(mask))
                else: mask_tensors.append(torch.ones((i.height, i.width), dtype=torch.float32))
                if resize_mode == "Don't Resize (First Image Only)": break
            except Exception as e: print(f"ComfyUI_Automation: Image Load Error on {url}: {e}")
        if not image_tensors: return (torch.zeros((1, 64, 64, 3)), torch.zeros((1, 64, 64)))
        return (torch.cat(image_tensors, dim=0), torch.cat(mask_tensors, dim=0))

# --- UTILITY NODES ---
class StringBatchToString:
    CATEGORY = "Automation/Utils"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "convert"
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "string_batch": ("STRING", {"forceInput": True, "tooltip": "Connect a list/batch of strings here (e.g., from a scraper's text output)."}),
                "separator": ("STRING", {"multiline": False, "default": "\\n\\n", "tooltip": "The characters to place between each string when joining them. Use \\n for a newline."}),
            }
        }
    def convert(self, string_batch, separator):
        processed_separator = separator.encode().decode('unicode_escape')
        if isinstance(string_batch, list): return (processed_separator.join(string_batch),)
        elif isinstance(string_batch, str): return (string_batch,)
        else: return ("",)

class SRTParser:
    """
    Parses a string in SRT (SubRip Subtitle) format and extracts the data for each entry.
    This version can also detect and handle silent pauses between subtitle entries.
    """
    CATEGORY = "Automation/Video"
    
    RETURN_TYPES = ("STRING", "INT", "INT", "INT")
    RETURN_NAMES = ("text_batch", "start_ms_batch", "end_ms_batch", "duration_ms_batch")
    FUNCTION = "parse_srt"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "srt_content": ("STRING", {"multiline": True, "dynamicPrompts": False, "tooltip": "Paste the entire content of your SRT file here."}),
                # --- NEW INPUT WIDGET ---
                "handle_pauses": (["Include Pauses", "Ignore Pauses"], {"default": "Include Pauses", "tooltip": "Determines how to handle silent gaps between subtitle entries. 'Include Pauses' adds blank text entries to maintain timing."}),
            }
        }

    def srt_time_to_ms(self, time_str):
        """Converts an SRT time string (HH:MM:SS,ms) to total milliseconds."""
        parts = re.split('[:,]', time_str)
        h, m, s, ms = map(int, parts)
        return (h * 3600 + m * 60 + s) * 1000 + ms

    def parse_srt(self, srt_content, handle_pauses):
        pattern = re.compile(
            r'(\d+)\n'
            r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\n'
            r'([\s\S]*?(?=\n\n|\Z))'
        )
        
        text_batch = []
        start_ms_batch = []
        end_ms_batch = []
        duration_ms_batch = []
        
        matches = list(pattern.finditer(srt_content)) # Use list to easily access next item
        
        last_end_time_ms = 0
        
        for i, match in enumerate(matches):
            text = match.group(4).strip().replace('\n', ' ')
            start_time_str = match.group(2)
            end_time_str = match.group(3)
            
            start_ms = self.srt_time_to_ms(start_time_str)
            end_ms = self.srt_time_to_ms(end_time_str)
            duration_ms = end_ms - start_ms

            # --- NEW PAUSE DETECTION LOGIC ---
            if handle_pauses == "Include Pauses" and start_ms > last_end_time_ms:
                pause_duration = start_ms - last_end_time_ms
                if pause_duration > 50: # Only add pauses longer than 50ms to avoid tiny gaps
                    print(f"ComfyUI_Automation: Detected a pause of {pause_duration}ms.")
                    # Add the pause entry
                    text_batch.append("") # Blank text for the pause
                    start_ms_batch.append(last_end_time_ms)
                    end_ms_batch.append(start_ms)
                    duration_ms_batch.append(pause_duration)

            # Add the actual subtitle entry
            text_batch.append(text)
            start_ms_batch.append(start_ms)
            end_ms_batch.append(end_ms)
            duration_ms_batch.append(duration_ms)
            
            last_end_time_ms = end_ms

        print(f"ComfyUI_Automation: Parsed {len(text_batch)} total entries (including pauses if enabled).")
        return (text_batch, start_ms_batch, end_ms_batch, duration_ms_batch)


class SRTSceneGenerator:
    """
    Generates a continuous batch of blank images based on timing data from an SRT file.
    It also outputs indexing information to help place content in the correct scenes.
    """
    CATEGORY = "Automation/Video"

    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("image_timeline", "start_frame_indices", "frame_counts")
    FUNCTION = "generate_scenes"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "duration_ms_batch": ("INT", {"forceInput": True, "tooltip": "Connect the duration_ms_batch output from the SRT Parser node here."}),
                "fps": ("INT", {"default": 24, "min": 1, "max": 120, "step": 1, "tooltip": "Frames per second for the final video. This determines how many frames are created for each duration."}),
                "width": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),
            }
        }

    def generate_scenes(self, duration_ms_batch, fps, width, height):
        if not isinstance(duration_ms_batch, list) or not duration_ms_batch:
            print("ComfyUI_Automation: SRTSceneGenerator received no valid duration batch.")
            return (torch.zeros((1, height, width, 3)), [0], [0])

        image_batch_list = []
        start_frame_indices = []
        frame_counts = []
        current_frame_index = 0

        for duration_ms in duration_ms_batch:
            # Calculate the number of frames for this scene
            num_frames = round((duration_ms / 1000.0) * fps)
            
            if num_frames <= 0:
                continue # Skip scenes that are too short to be a single frame

            # Create a single black frame
            black_frame = torch.zeros((1, height, width, 3), dtype=torch.float32)
            
            # Repeat the black frame to create the scene's image batch
            scene_batch = black_frame.repeat(num_frames, 1, 1, 1)
            
            image_batch_list.append(scene_batch)
            start_frame_indices.append(current_frame_index)
            frame_counts.append(num_frames)
            
            current_frame_index += num_frames
        
        if not image_batch_list:
            print("ComfyUI_Automation: All SRT durations were too short to generate frames.")
            return (torch.zeros((1, height, width, 3)), [0], [0])

        # Concatenate all scene batches into a single continuous timeline
        final_video_batch = torch.cat(image_batch_list, dim=0)

        print(f"ComfyUI_Automation: Generated a timeline of {current_frame_index} frames across {len(frame_counts)} scenes.")
        return (final_video_batch, start_frame_indices, frame_counts)