import feedparser
import re

class RssFeedReader:
    """
    A node to read RSS feeds, format the content, and create batches of data.
    """
    
    # Define where the node will appear in the ComfyUI add-node menu
    CATEGORY = "Automation"

    # Define the output types and names
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("raw_text", "formatted_text", "content_batch")
    
    # Define the function that will be executed
    FUNCTION = "read_feed"

    # Define the input types for the node
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "links": ("STRING", {
                    "multiline": True,
                    "default": "http://rss.cnn.com/rss/cnn_topstories.rss\nhttps://www.theverge.com/rss/index.xml"
                }),
                "max_entries": ("INT", {
                    "default": 5, 
                    "min": 1, 
                    "max": 100, 
                    "step": 1
                }),
                "batch_source": (["title", "summary", "link"],),
            }
        }

    def clean_html(self, raw_html):
        """A simple function to strip HTML tags from a string."""
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

    def read_feed(self, links, max_entries, batch_source):
        """
        The core logic of the node.
        It fetches RSS feeds, processes the entries, and returns the data in three formats.
        """
        # Split the input string into a list of URLs, ignoring empty lines
        urls = [url.strip() for url in links.splitlines() if url.strip()]
        
        all_raw_text = []
        all_formatted_text = []
        content_batch = []

        print(f"ComfyUI_Automation: Fetching from {len(urls)} RSS feed(s).")

        for url in urls:
            try:
                # Parse the feed using the feedparser library
                feed = feedparser.parse(url)
                
                # Check for errors in the feed
                if feed.bozo:
                    print(f"ComfyUI_Automation: Warning - Malformed feed at {url}. Reason: {feed.bozo_exception}")

                # Limit the number of entries to process
                entries_to_process = feed.entries[:max_entries]

                for entry in entries_to_process:
                    # Safely get attributes, providing an empty string as a fallback
                    title = getattr(entry, 'title', 'No Title')
                    link = getattr(entry, 'link', 'No Link')
                    summary_html = getattr(entry, 'summary', 'No Summary')
                    
                    # Clean the summary to remove HTML tags
                    summary = self.clean_html(summary_html)

                    # 1. Build the Raw Text Output (simple concatenation)
                    all_raw_text.append(f"{title}\n{summary}\n\n")
                    
                    # 2. Build the Formatted Text Output (more readable)
                    all_formatted_text.append(
                        f"Feed: {feed.feed.get('title', 'Unknown Feed')}\n"
                        f"Title: {title}\n"
                        f"Link: {link}\n"
                        f"Summary: {summary}\n"
                        f"------------------------------------\n"
                    )

                    # 3. Build the Content Batch (a list of strings)
                    # This uses the 'batch_source' input to decide what to put in the batch.
                    batch_item = getattr(entry, batch_source, '')
                    # If the item is the summary, we should use the cleaned version
                    if batch_source == 'summary':
                        content_batch.append(self.clean_html(batch_item))
                    else:
                        content_batch.append(batch_item)

            except Exception as e:
                print(f"ComfyUI_Automation: Error fetching or parsing feed at {url}: {e}")
                # Continue to the next URL even if one fails
                continue

        # Join the lists of strings into single strings for the first two outputs
        final_raw_text = "".join(all_raw_text)
        final_formatted_text = "".join(all_formatted_text)
        
        # The third output, 'content_batch', is returned as a Python list.
        # ComfyUI automatically handles a list as a batch input for other nodes.
        
        # We must return a tuple with our outputs in the correct order
        return (final_raw_text, final_formatted_text, content_batch)