import feedparser
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
import numpy as np
import torch
import io

# --- RSS FEEDER NODE (Updated with Skip Feature) ---
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
                # --- NEW INPUT WIDGET ---
                "skip_entries": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 1000, # Allow skipping a large number of entries
                    "step": 1
                }),
                "batch_source_1": (["title", "summary", "link"], {"default": "title"}),
                "batch_source_2": (["title", "summary", "link"], {"default": "summary"}),
                "output_mode": (["Concatenated String", "Batch Output"], {"default": "Concatenated String"})
            }
        }

    def clean_html(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html if raw_html else "")
        return cleantext

    # --- UPDATED FUNCTION SIGNATURE ---
    def read_feed(self, links, max_entries, skip_entries, batch_source_1, batch_source_2, output_mode):
        urls = [url.strip() for url in links.splitlines() if url.strip()]
        
        all_raw_output_items, all_formatted_text_items, content_batch_1_items, content_batch_2_items = [], [], [], []

        print(f"ComfyUI_Automation: Fetching from {len(urls)} RSS feed(s).")

        for url in urls:
            try:
                feed = feedparser.parse(url)
                if feed.bozo:
                    print(f"ComfyUI_Automation: Warning - Malformed feed at {url}. Reason: {feed.bozo_exception}")

                # --- UPDATED LOGIC TO HANDLE SKIPPING ---
                # Use Python's list slicing to skip and then take the max number of entries.
                start_index = skip_entries
                end_index = skip_entries + max_entries
                entries_to_process = feed.entries[start_index:end_index]
                # --- END OF UPDATED LOGIC ---

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

# --- WEB SCRAPER NODES (Unchanged) ---
class SimpleWebScraper:
    # ... (This class is unchanged) ...
    CATEGORY = "Automation/Web"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("extracted_texts", "image_urls")
    FUNCTION = "scrape_simple"
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"url": ("STRING", {"multiline": False, "default": ""}),}}
    def _make_absolute_url(self, base_url, link):
        return urljoin(base_url, link)
    def scrape_simple(self, url):
        url_list = [url] if isinstance(url, str) else url
        all_texts, all_image_urls = [], []
        for single_url in url_list:
            print(f"ComfyUI_Automation: Simple Scraper processing URL: {single_url}")
            headers = {'User-Agent': 'Mozilla/5.0'}
            try:
                response = requests.get(single_url, headers=headers, timeout=10)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"ComfyUI_Automation: Error fetching URL {single_url}: {e}")
                continue
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""
            all_texts.append(page_text)
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    absolute_url = self._make_absolute_url(single_url, src)
                    if absolute_url not in all_image_urls: all_image_urls.append(absolute_url)
        print(f"ComfyUI_Automation: Simple Scraper finished. Extracted text from {len(all_texts)} pages and found {len(all_image_urls)} total image links.")
        return (all_texts, all_image_urls)


class TargetedWebScraper:
    # ... (This class is unchanged) ...
    CATEGORY = "Automation/Web"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("extracted_text", "image_urls")
    FUNCTION = "scrape_targeted"
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"url": ("STRING", {"multiline": False, "default": ""}), "selectors": ("STRING", {"multiline": True, "default": ".c-entry-box--compact__title"}),}}
    def _make_absolute_url(self, base_url, link):
        return urljoin(base_url, link)
    def scrape_targeted(self, url, selectors):
        url_list = [url] if isinstance(url, str) else url
        final_text_batch, final_image_batch = [], []
        selector_list = [s.strip() for s in selectors.splitlines() if s.strip()]
        if not selector_list:
            print("ComfyUI_Automation: Targeted Scraper received no selectors.")
            return ([], [])
        for single_url in url_list:
            print(f"ComfyUI_Automation: Targeted Scraper processing URL: {single_url}")
            headers = {'User-Agent': 'Mozilla/5.0'}
            try:
                response = requests.get(single_url, headers=headers, timeout=10)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"ComfyUI_Automation: Error fetching URL {single_url}: {e}")
                continue
            soup = BeautifulSoup(response.content, 'html.parser')
            found_elements = soup.select(','.join(selector_list))
            for element in found_elements:
                text = element.get_text(separator=' ', strip=True)
                if text: final_text_batch.append(text)
                for img in element.find_all('img'):
                    src = img.get('src')
                    if src:
                        absolute_url = self._make_absolute_url(single_url, src)
                        if absolute_url not in final_image_batch: final_image_batch.append(absolute_url)
        print(f"ComfyUI_Automation: Targeted Scraper finished. Found {len(final_text_batch)} text snippets and {len(final_image_batch)} image links across all pages.")
        return (final_text_batch, final_image_batch)