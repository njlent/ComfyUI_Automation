# File: ComfyUI_Automation/README.md

# ComfyUI Automation Node Pack

This is a collection of custom nodes for ComfyUI designed to automate and streamline creative workflows by fetching data from web sources like RSS feeds and web pages.

## Installation

1.  Navigate to your `ComfyUI/custom_nodes/` directory.
2.  Clone this repository into that directory:
    ```bash
    git clone <your-repository-url-here> ComfyUI_Automation
    ```
    (Or, if you downloaded the files manually, just place the `ComfyUI_Automation` folder here).
3.  Restart ComfyUI. The ComfyUI-Manager (or the terminal) should detect the `requirements.txt` file and prompt you to install the necessary dependencies (`feedparser`, `requests`, `beautifulsoup4`, `Pillow`).
4.  If the dependencies are not installed automatically, you can install them manually by opening a terminal/command prompt, navigating to your ComfyUI installation, and running:
    ```bash
    pip install -r ComfyUI/custom_nodes/ComfyUI_Automation/requirements.txt
    ```
5.  Restart ComfyUI one more time after the dependencies are installed. Your new nodes will appear in the "Automation" category when you right-click the canvas.

---

## Nodes

The nodes are organized into sub-categories for ease of use.

### Automation/RSS

#### 📰 RSS Feed Reader
Fetches and parses entries from one or more RSS feeds.

*   **Inputs**:
    *   `links`: A multiline text box for one or more RSS feed URLs.
    *   `max_entries`: The maximum number of entries to fetch from *each* feed.
    *   `skip_entries`: Skips the first N entries. Useful for paging through a feed.
    *   `batch_source_1` / `batch_source_2`: Select the content (`title`, `summary`, or `link`) for the two independent batch outputs.
    *   `output_mode`: `Batch Output` returns `raw_output` and `formatted_text` as batches. `Concatenated String` returns them as single large strings.
*   **Outputs**:
    *   `raw_output`: The full, raw JSON data for each entry.
    *   `formatted_text`: A human-readable summary of each entry.
    *   `content_batch_1` / `content_batch_2`: Batches of strings containing the content specified by the `batch_source` inputs.

### Automation/Web

#### 🕸️ Simple Web Scraper
A basic scraper that grabs all text and all image links from one or more URLs.

*   **Inputs**:
    *   `url`: A single URL string or a batch of URL strings.
*   **Outputs**:
    *   `extracted_texts`: A batch of strings, where each string is the entire text content of a scraped page.
    *   `image_urls`: A batch containing every image URL found across all scraped pages.

#### 🎯 Targeted Web Scraper
A powerful scraper that extracts content from specific parts of a page using CSS selectors, with the ability to ignore unwanted elements.

*   **Inputs**:
    *   `url`: A single URL string or a batch of URL strings.
    *   `selectors`: The CSS selectors for the content you **want** to extract (e.g., `.article-body`, `h1`).
    *   `ignore_selectors`: The CSS selectors for content you want to **remove before** extraction (e.g., `nav`, `footer`, `.ads`).
*   **Outputs**:
    *   `extracted_text`: A batch of strings containing the text from the targeted elements.
    *   `image_urls`: A batch of image URLs found *only within* the targeted elements.

### Automation/Image

#### 🖼️ Load Image From URL
Downloads one or more images from URLs and prepares them as a standard ComfyUI `IMAGE` batch.

*   **Inputs**:
    *   `image_url`: A single URL string or a batch of URL strings (e.g., from a scraper node).
    *   `resize_mode`: Determines how to handle images of different sizes.
        *   `Don't Resize (First Image Only)`: **(Not Batch Compatible)** Loads the first valid image at its original resolution and stops.
        *   `Stretch`: Forces all images to the target size, ignoring aspect ratio.
        *   `Crop (Center)`: Resizes and crops to fill the target size, preserving aspect ratio.
        *   `Pad (Black)`: Resizes to fit inside the target size, preserving aspect ratio and adding black bars.
    *   `target_width` / `target_height`: The uniform dimensions for the output image batch.
*   **Outputs**:
    *   `IMAGE`: A standard ComfyUI image batch tensor.
    *   `MASK`: A corresponding mask batch tensor.

### Automation/Utils

#### 📜 Batch to String
A utility node to convert a list/batch of strings into a single string. This is the perfect "bridge" to connect batch outputs to nodes that expect a single string input.

*   **Inputs**:
    *   `string_batch`: A batch of strings (e.g., from the `extracted_text` output of a scraper).
    *   `separator`: The characters to place between each string when joining them. Default is `\n\n` (a double newline).
*   **Outputs**:
    *   `string`: A single string containing all the items from the batch, joined by the separator.