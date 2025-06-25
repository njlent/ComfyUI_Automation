# File: ComfyUI_Automation/nodes.py (Final Version with All Features)

# --- IMPORTS ---
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

# --- RSS FEEDER NODE (Unchanged) ---
class RssFeedReader:
    CATEGORY = "Automation/RSS"
    RETURN_TYPES, RETURN_NAMES = ("STRING", "STRING", "STRING", "STRING"), ("raw_output", "formatted_text", "content_batch_1", "content_batch_2")
    FUNCTION = "read_feed"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"links": ("STRING", {"multiline": True, "default": ""}),"max_entries": ("INT", {"default": 3, "min": 1, "max": 100, "step": 1}),"skip_entries": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1}),"batch_source_1": (["title", "summary", "link"], {"default": "title"}),"batch_source_2": (["title", "summary", "link"], {"default": "summary"}),"output_mode": (["Concatenated String", "Batch Output"], {"default": "Concatenated String"})}}
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

# --- WEB SCRAPER NODES (Targeted Scraper is Upgraded) ---
class SimpleWebScraper:
    CATEGORY = "Automation/Web"
    RETURN_TYPES, RETURN_NAMES = ("STRING", "STRING"), ("extracted_texts", "image_urls")
    FUNCTION = "scrape_simple"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"url": ("STRING", {"multiline": False, "default": ""})}}
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
    """
    A targeted web scraper that extracts content from specific areas of one or
    more pages, with an option to ignore/remove elements first.
    """
    CATEGORY = "Automation/Web"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("extracted_text", "image_urls")
    FUNCTION = "scrape_targeted"
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "url": ("STRING", {"multiline": False, "default": ""}),
                "selectors": ("STRING", {"multiline": True, "default": "body"}),
                # --- NEW INPUT ---
                "ignore_selectors": ("STRING", {
                    "multiline": True,
                    "default": "nav, footer, .ad-container"
                }),
            }
        }
    
    def _make_absolute_url(self, base_url, link): return urljoin(base_url, link)

    def scrape_targeted(self, url, selectors, ignore_selectors):
        url_list = [url] if isinstance(url, str) else url
        final_text_batch, final_image_batch = [], []
        
        selector_list = [s.strip() for s in selectors.splitlines() if s.strip()]
        ignore_selector_list = [s.strip() for s in ignore_selectors.splitlines() if s.strip()]

        if not selector_list: return ([], [])

        for single_url in url_list:
            if not single_url: continue
            try:
                response = requests.get(single_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

                # --- NEW: IGNORE/REMOVE ELEMENTS LOGIC ---
                if ignore_selector_list:
                    print(f"ComfyUI_Automation: Removing {len(ignore_selector_list)} types of ignored elements...")
                    for ignored in soup.select(','.join(ignore_selector_list)):
                        ignored.decompose() # This removes the element from the parse tree

                for element in soup.select(','.join(selector_list)):
                    if text := element.get_text(separator=' ', strip=True):
                        final_text_batch.append(text)
                    for img in element.find_all('img'):
                        if src := img.get('src'):
                            abs_url = self._make_absolute_url(single_url, src)
                            if abs_url not in final_image_batch:
                                final_image_batch.append(abs_url)

            except Exception as e: print(f"ComfyUI_Automation: Targeted Scraper Error on {single_url}: {e}")
        return (final_text_batch, final_image_batch)

# --- IMAGE LOADER NODE (Upgraded with "Don't Resize" option) ---
class LoadImageFromURL:
    """
    Downloads an image, optionally resizes it, and provides it as a tensor.
    "Don't Resize" option is not batch compatible and will only process the first valid image.
    """
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image_from_url"
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_url": ("STRING", {"multiline": False, "default": ""}),
                # --- NEW OPTION ADDED ---
                "resize_mode": (["Don't Resize (First Image Only)", "Stretch", "Crop (Center)", "Pad (Black)"], {
                    "default": "Pad (Black)"
                }),
                "target_width": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),
                "target_height": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),
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
                i = Image.open(io.BytesIO(response.content))
                original_mode = i.mode
                
                # --- UPDATED RESIZING LOGIC ---
                if resize_mode == "Stretch":
                    i = i.resize(target_size, Image.Resampling.LANCZOS)
                elif resize_mode == "Crop (Center)":
                    i = ImageOps.fit(i, target_size, Image.Resampling.LANCZOS)
                elif resize_mode == "Pad (Black)":
                    img_copy = i.copy(); img_copy.thumbnail(target_size, Image.Resampling.LANCZOS)
                    background = Image.new('RGB', target_size, (0, 0, 0))
                    paste_pos = ((target_size[0] - img_copy.width) // 2, (target_size[1] - img_copy.height) // 2)
                    background.paste(img_copy, paste_pos); i = background
                # If "Don't Resize" is selected, we do nothing and use the original image 'i'.
                
                i = i.convert("RGB")
                image = np.array(i).astype(np.float32) / 255.0
                image_tensor = torch.from_numpy(image)[None,]
                image_tensors.append(image_tensor)
                
                if original_mode == 'RGBA':
                    mask = np.array(Image.open(io.BytesIO(response.content)).getchannel('A')).astype(np.float32) / 255.0
                    if resize_mode != "Don't Resize (First Image Only)": # Also resize the mask if needed
                         mask_img = Image.fromarray(mask); mask_img = mask_img.resize(target_size, Image.Resampling.LANCZOS)
                         mask = np.array(mask_img)
                    mask_tensors.append(torch.from_numpy(mask))
                else:
                    mask_tensors.append(torch.ones((i.height, i.width), dtype=torch.float32))

                # --- BATCH-LIMITING LOGIC for "Don't Resize" ---
                if resize_mode == "Don't Resize (First Image Only)":
                    print("ComfyUI_Automation: 'Don't Resize' selected. Processing first valid image only.")
                    break # Exit the loop after the first successful image
                    
            except Exception as e: print(f"ComfyUI_Automation: Image Load Error on {url}: {e}")

        if not image_tensors:
            print("ComfyUI_Automation: No images were successfully loaded.")
            return (torch.zeros((1, 64, 64, 3)), torch.zeros((1, 64, 64)))
        
        return (torch.cat(image_tensors, dim=0), torch.cat(mask_tensors, dim=0))
    
    
class StringBatchToString:
    """
    A utility node to convert a batch of strings (a list) into a single string,
    with a user-defined separator.
    """
    CATEGORY = "Automation/Utils"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "convert"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "string_batch": ("STRING", {"forceInput": True}),
                "separator": ("STRING", {"multiline": False, "default": "\\n\\n"}), # Default to a double newline
            }
        }

    def convert(self, string_batch, separator):
        # The separator widget uses \n for newlines, so we need to un-escape it.
        # This allows users to type "\n" for a newline, "\\" for a literal backslash, etc.
        processed_separator = separator.encode().decode('unicode_escape')

        if isinstance(string_batch, list):
            # If the input is a list, join it.
            result_string = processed_separator.join(string_batch)
            return (result_string,)
        elif isinstance(string_batch, str):
            # If it's already a string, just pass it through.
            return (string_batch,)
        else:
            # If it's something else, return an empty string to avoid errors.
            return ("",)