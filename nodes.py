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