# File: ComfyUI_Automation/nodes.py (Final Corrected Version)

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

# --- RSS FEEDER NODE (Reverted to working, readable version) ---
class RssFeedReader:
    """
    A node to read RSS feeds. It provides the raw entry data as a JSON string,
    a human-readable formatted text version, and two independent, user-configurable
    content batches. Includes a feature to skip the first N entries.
    """
    CATEGORY = "Automation/RSS"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("raw_output", "formatted_text", "content_batch_1", "content_batch_2")
    FUNCTION = "read_feed"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "links": ("STRING", {"multiline": True, "default": "http://rss.cnn.com/rss/cnn_topstories.rss\nhttps://www.theverge.com/rss/index.xml"}),
                "max_entries": ("INT", {"default": 3, "min": 1, "max": 100, "step": 1}),
                "skip_entries": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1}),
                "batch_source_1": (["title", "summary", "link"], {"default": "title"}),
                "batch_source_2": (["title", "summary", "link"], {"default": "summary"}),
                "output_mode": (["Concatenated String", "Batch Output"], {"default": "Concatenated String"})
            }
        }

    def clean_html(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html if raw_html else "")
        return cleantext

    def read_feed(self, links, max_entries, skip_entries, batch_source_1, batch_source_2, output_mode):
        urls = [url.strip() for url in links.splitlines() if url.strip()]
        all_raw_output_items, all_formatted_text_items, content_batch_1_items, content_batch_2_items = [], [], [], []
        print(f"ComfyUI_Automation: Fetching from {len(urls)} RSS feed(s).")
        for url in urls:
            try:
                feed = feedparser.parse(url)
                if feed.bozo:
                    print(f"ComfyUI_Automation: Warning - Malformed feed at {url}. Reason: {feed.bozo_exception}")
                start_index = skip_entries
                end_index = skip_entries + max_entries
                entries_to_process = feed.entries[start_index:end_index]
                for entry in entries_to_process:
                    raw_entry_json = json.dumps(entry, indent=2)
                    all_raw_output_items.append(raw_entry_json)
                    title, link, summary_html = getattr(entry, 'title', 'No Title'), getattr(entry, 'link', 'No Link'), getattr(entry, 'summary', 'No Summary')
                    summary = self.clean_html(summary_html)
                    all_formatted_text_items.append(f"Feed: {feed.feed.get('title', 'Unknown Feed')}\nTitle: {title}\nLink: {link}\nSummary: {summary}\n------------------------------------")
                    batch_1_value = getattr(entry, batch_source_1, '')
                    content_batch_1_items.append(self.clean_html(batch_1_value) if batch_source_1 == 'summary' else batch_1_value)
                    batch_2_value = getattr(entry, batch_source_2, '')
                    content_batch_2_items.append(self.clean_html(batch_2_value) if batch_source_2 == 'summary' else batch_2_value)
            except Exception as e:
                print(f"ComfyUI_Automation: Error fetching or parsing feed at {url}: {e}")
                continue
        if output_mode == "Concatenated String":
            final_raw_output = "\n\n---\n[NEXT ENTRY]\n---\n\n".join(all_raw_output_items)
            final_formatted_text = "\n".join(all_formatted_text_items)
            return (final_raw_output, final_formatted_text, content_batch_1_items, content_batch_2_items)
        else:
            return (all_raw_output_items, all_formatted_text_items, content_batch_1_items, content_batch_2_items)

# --- WEB SCRAPER NODES (Unchanged from previous working version) ---
class SimpleWebScraper:
    CATEGORY = "Automation/Web"
    RETURN_TYPES, RETURN_NAMES = ("STRING", "STRING"), ("extracted_texts", "image_urls")
    FUNCTION = "scrape_simple"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"url": ("STRING", {"multiline": False, "default": ""})}}
    def _make_absolute_url(self, b, l): return urljoin(b, l)
    def scrape_simple(self, url):
        url_list, all_texts, all_image_urls = [url] if isinstance(url, str) else url, [], []
        for single_url in url_list:
            if not single_url: continue
            try:
                response = requests.get(single_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10); response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                all_texts.append(soup.body.get_text(separator=' ', strip=True) if soup.body else "")
                for img in soup.find_all('img'):
                    if src := img.get('src'):
                        if (abs_url := self._make_absolute_url(single_url, src)) not in all_image_urls: all_image_urls.append(abs_url)
            except Exception as e: print(f"ComfyUI_Automation: Error fetching {single_url}: {e}")
        return (all_texts, all_image_urls)

class TargetedWebScraper:
    CATEGORY = "Automation/Web"
    RETURN_TYPES, RETURN_NAMES = ("STRING", "STRING"), ("extracted_text", "image_urls")
    FUNCTION = "scrape_targeted"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"url": ("STRING", {"multiline": False, "default": ""}), "selectors": ("STRING", {"multiline": True, "default": ""})}}
    def _make_absolute_url(self, b, l): return urljoin(b, l)
    def scrape_targeted(self, url, selectors):
        url_list, final_text_batch, final_image_batch, selector_list = [url] if isinstance(url, str) else url, [], [], [s.strip() for s in selectors.splitlines() if s.strip()]
        if not selector_list: return ([], [])
        for single_url in url_list:
            if not single_url: continue
            try:
                response = requests.get(single_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10); response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                for element in soup.select(','.join(selector_list)):
                    if text := element.get_text(separator=' ', strip=True): final_text_batch.append(text)
                    for img in element.find_all('img'):
                        if src := img.get('src'):
                            if (abs_url := self._make_absolute_url(single_url, src)) not in final_image_batch: final_image_batch.append(abs_url)
            except Exception as e: print(f"ComfyUI_Automation: Error fetching {single_url}: {e}")
        return (final_text_batch, final_image_batch)

# --- IMAGE LOADER NODE (Upgraded with Resizing) ---
class LoadImageFromURL:
    """
    Downloads an image from a URL, resizes it to a uniform size, and provides it
    as an IMAGE and MASK tensor. Handles single URLs or batches.
    """
    CATEGORY = "Automation/Image"
    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image_from_url"
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_url": ("STRING", {"multiline": False, "default": ""}),
                "resize_mode": (["Stretch", "Crop (Center)", "Pad (Black)"], {"default": "Pad (Black)"}),
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
            if not url or not url.strip().startswith(('http://', 'https://')):
                print(f"ComfyUI_Automation: Invalid or empty URL '{url}', skipping.")
                continue
            try:
                print(f"ComfyUI_Automation: Downloading image from {url}")
                response = requests.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                
                i = Image.open(io.BytesIO(response.content))
                
                if resize_mode == "Stretch":
                    i = i.resize(target_size, Image.Resampling.LANCZOS)
                elif resize_mode == "Crop (Center)":
                    i = ImageOps.fit(i, target_size, Image.Resampling.LANCZOS)
                elif resize_mode == "Pad (Black)":
                    img_copy = i.copy()
                    img_copy.thumbnail(target_size, Image.Resampling.LANCZOS)
                    background = Image.new('RGB', target_size, (0, 0, 0))
                    paste_pos = ((target_size[0] - img_copy.width) // 2, (target_size[1] - img_copy.height) // 2)
                    background.paste(img_copy, paste_pos)
                    i = background
                
                i = i.convert("RGB")
                
                image = np.array(i).astype(np.float32) / 255.0
                image_tensor = torch.from_numpy(image)[None,]
                image_tensors.append(image_tensor)
                
                if 'A' in i.getbands() and i.mode == 'RGBA':
                    mask_np = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                    mask_tensor = torch.from_numpy(mask_np)
                else:
                    mask_tensor = torch.ones((i.height, i.width), dtype=torch.float32)
                mask_tensors.append(mask_tensor)

            except Exception as e:
                print(f"ComfyUI_Automation: Failed to process image from {url}: {e}")

        if not image_tensors:
            print("ComfyUI_Automation: No images were successfully loaded.")
            blank_image = torch.zeros((1, target_height, target_width, 3), dtype=torch.float32)
            blank_mask = torch.zeros((1, target_height, target_width), dtype=torch.float32)
            return (blank_image, blank_mask)
        
        final_image_batch = torch.cat(image_tensors, dim=0)
        final_mask_batch = torch.cat(mask_tensors, dim=0)
        
        print(f"ComfyUI_Automation: Successfully loaded and resized {len(final_image_batch)} image(s) to {target_width}x{target_height}.")
        return (final_image_batch, final_mask_batch)