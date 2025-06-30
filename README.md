# ComfyUI Automation Node Pack

This is a collection of custom nodes for ComfyUI designed to automate and streamline creative workflows by fetching data from web sources, processing text and images, and building video timelines from scripts.

---

## Node Glossary

*   [**RSS Feed Reader**](#-rss-feed-reader)
*   [**Simple Web Scraper**](#-simple-web-scraper)
*   [**Targeted Web Scraper**](#-targeted-web-scraper)
*   [**Load Image From URL**](#-load-image-from-url)
*   [**Layered Image Processor**](#️-layered-image-processor)
*   [**Text on Image**](#️-text-on-image)
*   [**SRT Parser**](#-srt-parser)
*   [**SRT Scene Generator**](#️-srt-scene-generator)
*   [**Image Batch Repeater**](#-image-batch-repeater)
*   [**Batch to String**](#-batch-to-string)

---

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

## Node Descriptions

### Automation/RSS

#### 📰 RSS Feed Reader
*Category: `Automation/RSS`*

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
*Category: `Automation/Web`*

A basic scraper that grabs all text and all image links from one or more URLs.

*   **Inputs**:
    *   `url`: A single URL string or a batch of URL strings.
*   **Outputs**:
    *   `extracted_texts`: A batch of strings, where each string is the entire text content of a scraped page.
    *   `image_urls`: A batch containing every image URL found across all scraped pages.

#### 🎯 Targeted Web Scraper
*Category: `Automation/Web`*

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
*Category: `Automation/Image`*

Downloads one or more images from URLs and prepares them as a standard ComfyUI `IMAGE` batch.

*   **Inputs**:
    *   `image_url`: A single URL string or a batch of URL strings.
    *   `resize_mode`: Determines how to handle images of different sizes. `Don't Resize (First Image Only)` is not batch-compatible. Other options include `Stretch`, `Crop (Center)`, and `Pad (Black)`.
    *   `target_width` / `target_height`: The uniform dimensions for the output image batch.
*   **Outputs**:
    *   `IMAGE`: A standard ComfyUI image batch tensor.
    *   `MASK`: A corresponding mask batch tensor.

#### 🖼️ Layered Image Processor
*Category: `Automation/Image`*

Creates a layered image effect by placing a padded version of an image on top of a blurred, full-screen version of the same image. Fully batch-aware.

*   **Inputs**:
    *   `image`: The source image or image batch.
    *   `width` / `height`: The dimensions of the final output canvas.
    *   `blur_radius`: The strength of the Gaussian blur on the background layer.
    *   `resampling_method`: The algorithm for resizing (`LANCZOS`, `BICUBIC`, etc.).
*   **Outputs**:
    *   `image`: A batch of images with the layered effect applied.

#### ✍️ Text on Image
*Category: `Automation/Image`*

Draws text onto an image with various formatting options. Intelligently handles batches of images and/or text.

*   **Inputs**:
    *   `image`: The image or image batch to draw on.
    *   `text`: The text string or batch of strings to draw.
    *   `font_name`, `font_size`, `font_color`: Standard font styling options.
    *   `horizontal_align`, `vertical_align`, `margin`, `x_position`, `y_position`: Powerful controls for positioning the text.
*   **Outputs**:
    *   `image`: The image batch with text applied.

### Automation/Video

#### 🎬 SRT Parser
*Category: `Automation/Video`*

Parses SRT (subtitle) formatted text to extract timing and content for video creation.

*   **Inputs**:
    *   `srt_content`: The full text of an `.srt` file.
    *   `handle_pauses`: `Include Pauses` creates blank entries for silent gaps to maintain perfect timing. `Ignore Pauses` extracts only the dialogue.
*   **Outputs**:
    *   `text_batch`: The text content of each subtitle/pause.
    *   `start_ms_batch`, `end_ms_batch`, `duration_ms_batch`: Timing data for each section in milliseconds.
    *   `section_count`: A total count of all outputted sections (subtitles + pauses).

#### 🎞️ SRT Scene Generator
*Category: `Automation/Video`*

Generates a timeline of blank frames based on timing data from the `SRT Parser`. This creates the foundational "video canvas".

*   **Inputs**:
    *   `duration_ms_batch`: Connect the `duration_ms_batch` from the `SRT Parser`.
    *   `fps`, `width`, `height`: Standard video settings.
*   **Outputs**:
    *   `image_timeline`: A single, long batch of blank frames representing the entire video duration.
    *   `start_frame_indices`: The starting frame number for each scene.
    *   `frame_counts`: The number of frames in each scene.

#### 🔂 Image Batch Repeater
*Category: `Automation/Video`*

The core assembly node. It takes a batch of content images and repeats them according to a list of frame counts, creating a video timeline.

*   **Inputs**:
    *   `image`: A batch of content images (e.g., generated from the `text_batch` of the SRT Parser).
    *   `repeat_counts`: The list of frame durations. Connect the `frame_counts` from the `SRT Scene Generator` here.
*   **Outputs**:
    *   `image_timeline`: A finished video timeline with your content correctly placed and timed.

### Automation/Utils

#### 📜 Batch to String
*Category: `Automation/Utils`*

A utility node to convert a list/batch of strings into a single string. This is a crucial "bridge" for connecting batch outputs to nodes that expect a single string input.

*   **Inputs**:
    *   `string_batch`: A batch of strings (e.g., from the `extracted_text` output of a scraper).
    *   `separator`: The characters to place between each string when joining them.
*   **Outputs**:
    *   `string`: A single string containing all the items from the batch, joined by the separator.