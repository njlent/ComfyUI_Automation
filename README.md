# ComfyUI Automation Node Pack

This is a collection of custom nodes for ComfyUI designed to automate and streamline creative workflows by fetching data from web sources, processing text and images, and building complex, animated video timelines from scripts.

---

## Node Glossary

*   [**RSS Feed Reader**](#-rss-feed-reader)
*   [**Simple Web Scraper**](#️-simple-web-scraper)
*   [**Targeted Web Scraper**](#-targeted-web-scraper)
*   [**Load Image From URL**](#️-load-image-from-url)
*   [**Layered Image Processor**](#️-layered-image-processor)
*   [**Text on Image**](#️-text-on-image)
*   [**Paste Text on Image Batch**](#️-paste-text-on-image-batch)
*   [**Animate Text on Image**](#️-animate-text-on-image)
*   [**Transform Paster (Static)**](#-transform-paster-static)
*   [**Transform Paster (Batch)**](#-transform-paster-batch)
*   [**Gaussian Blur**](#-gaussian-blur)
*   [**Animate Gaussian Blur**](#-animate-gaussian-blur)
*   [**Green Screen Keyer**](#-green-screen-keyer)
*   [**Webhook Uploader**](#-webhook-uploader)
*   [**S3 Uploader**](#-s3-uploader)
*   [**SRT Parser**](#-srt-parser)
*   [**SRT Scene Generator**](#️-srt-scene-generator)
*   [**Image Batch Repeater**](#-image-batch-repeater)
*   [**Mask Batch Repeater**](#-mask-batch-repeater)
*   [**Audio Reactive Paster**](#-audio-reactive-paster)
*   [**Image Selector by Index**](#️-image-selector-by-index)
*   [**Get Last Image from Batch**](#️-get-last-image-from-batch)
*   [**Time Scheduler**](#-time-scheduler)
*   [**String to Integer**](#-string-to-integer)
*   [**Batch to String**](#-batch-to-string)
*   [**String Literal to List Converter**](#-string-literal-to-list-converter)
*   [**Image/Mask Batch Combiner**](#-imagemask-batch-combiner)
*   [**Image Batch Concatenator**](#-image-batch-concatenator)
*   [**Memory Purge**](#-memory-purge)
### Experimental nodes
*   [**Direct TikTok Uploader**](#-direct-tiktok-uploader-experimental)
*   [**Scheduled TikTok Uploader**](#-scheduled-tiktok-uploader-experimental)

---

## Installation

1.  Navigate to your `ComfyUI/custom_nodes/` directory.
2.  Clone this repository into that directory:
    ```bash
    git clone https://github.com/njlent/ComfyUI_Automation ComfyUI_Automation
    ```
    (Or, if you downloaded the files manually, just place the `njlent-comfyui_automation` folder here).
3.  Restart ComfyUI. The ComfyUI-Manager (or the terminal) should detect the `requirements.txt` file and prompt you to install the necessary dependencies (`feedparser`, `requests`, `beautifulsoup4`, `Pillow`, `torchaudio`, `pandas`, `scipy`, `boto3`, `pytz`, `psutil`).
4.  If the dependencies are not installed automatically, you can install them manually by opening a terminal/command prompt, navigating to your ComfyUI installation, and running:
    ```bash
    pip install -r ComfyUI/custom_nodes/njlent-comfyui_automation/requirements.txt
    ```
5.  **For Experimental TikTok Nodes (Optional):** If you wish to use the direct TikTok uploader nodes, you must install additional dependencies. Run the following command in your terminal:
    ```bash
    pip install tiktok-uploader selenium
    ```
    **Note:** These nodes are experimental and may break if TikTok changes its website.
6.  Restart ComfyUI one more time after all dependencies are installed. Your new nodes will appear in the "Automation" category when you right-click the canvas.

---

## Node Descriptions

### Automation/RSS

#### 📰 RSS Feed Reader
*Category: `Automation/RSS`*
Fetches and parses entries from one or more RSS feeds.

### Automation/Web

#### 🕸️ Simple Web Scraper
*Category: `Automation/Web`*
A basic scraper that grabs all text and all image links from one or more URLs.

#### 🎯 Targeted Web Scraper
*Category: `Automation/Web`*
A powerful scraper that gives you fine-grained control to extract content from specific parts of a web page using CSS selectors, while simultaneously removing unwanted content.
*   **How it works**:
    1.  First, it finds all elements matching the `ignore_selectors` and completely removes them from the page's code. This is ideal for cleaning out ads, navigation bars, footers, or "related posts" sections.
    2.  Then, on the cleaned-up page, it finds all elements matching your main `selectors`.
    3.  Finally, it extracts all the text and image URLs from within those main elements.
*   **Finding Selectors**: Use your browser's "Inspect" or "Developer Tools" feature. Right-click the element you want to scrape (or ignore) and choose "Inspect". You can then see its tag (like `div`, `p`, `article`) and its attributes (like `class="content-body"` or `id="main"`).

### Automation/Image

#### 🖼️ Load Image From URL
*Category: `Automation/Image`*
Downloads one or more images from URLs and prepares them as a standard ComfyUI `IMAGE` batch.

#### 🖼️ Layered Image Processor
*Category: `Automation/Image`*
Creates a layered image effect by placing a scaled version of an image on top of a blurred, full-screen version of the same image. Fully batch-aware, it correctly handles both upscaling and downscaling of the foreground image to fit the canvas.
*   **Features**: Includes `x_offset` and `y_offset` inputs to precisely position the foreground layer off-center.

#### ✍️ Text on Image
*Category: `Automation/Image`*
A highly advanced node for drawing stylized static text onto an image. It is fully batch-aware and packed with professional features.
*   **Emoji Support**: Automatically detects and renders emojis using your system's native emoji font.
*   **Formatting**: Full control over font, size, color, alignment, and positioning.
*   **Word Wrap**: `wrap_width` input for automatic word wrapping.
*   **Line Height**: `line_height_multiplier` for precise control over spacing between lines.
*   **Styling**: Choose `None`, `Background Block`, `Drop Shadow`, or `Stroke` with full control.

#### ✍️ Paste Text on Image Batch
*Category: `Automation/Image`*
A powerful compositing node that pastes formatted text onto a background image batch or video timeline. This node is timeline-aware.
*   **Inputs**: `background_image`, `text`, optional `text_durations`, and `wrap_width`.

#### ✍️ Animate Text on Image
*Category: `Automation/Image`*
A comprehensive motion graphics node for creating animated text on a video timeline. It handles batches of text with synchronized timing and features advanced styling.
*   **Animation**: Choose `Typewriter` or `Reveal` with precise speed controls.
*   **Timeline Control**: Takes `text` and optional `text_durations` to animate multiple text blocks in sequence. Correctly handles single durations to show text for a specific time and then hide it.
*   **Advanced Styling**: Full emoji support and all styling from the static `Text on Image` node, including per-line background blocks, drop shadows, and strokes, with correct transparency and layering.
*   **Memory Efficient**: Designed to work in-place on the input tensor, allowing multiple text animations to be chained without running out of RAM.

#### 🔧 Transform Paster (Static)
*Category: `Automation/Image`*
A core compositing tool for **single images**. It takes a background image, an overlay image, and a mask, and provides precise controls for transforming the overlay before pasting. Renamed from `Transform Paster` for clarity.
*   **Controls**: Full control over `size`, `rotation`, and `x_offset`/`y_offset` position.
*   **Use Case**: Perfect for creating static compositions or preparing elements for a video workflow.

#### 🔧 Transform Paster (Batch)
*Category: `Automation/Image`*
A powerful and **memory-efficient** node for compositing video timelines. It transforms and pastes an `overlay_image` batch onto a `background_image` batch with precise timing controls.
*   **One-Shot Pasting**: This node applies the overlay sequence only once. It does **not** loop.
*   **Timing Controls**: `alignment_mode` (`Paste at Start`/`End`) and `start_frame_offset` allow for precise placement of the overlay sequence on the timeline.
*   **Memory-Efficient**: Processes one frame at a time, keeping RAM usage low and constant.
*   **Use Case**: Ideal for non-looping effects like title cards, temporary graphics, or "subscribe" animations.

#### ✨ Gaussian Blur
*Category: `Automation/Image`*
A simple and efficient node to apply a Gaussian blur effect to an image or a batch of images.

#### ✨ Animate Gaussian Blur
*Category: `Automation/Image`*
A motion graphics node that applies a Gaussian blur effect to a video timeline, with the blur strength animating smoothly from `0` to a `max_radius` over the duration of the clip.
*   **Use Case**: Perfect for creating dynamic focus pulls, dream-like intros, or smooth transitions.

#### 🟩 Green Screen Keyer
*Category: `Automation/Image`*
A node for performing chroma keying on an image or video timeline.
*   **How it works**: Uses `key_color`, `threshold`, and `softness` to generate a smooth, high-quality mask.
*   **Use Case**: The primary tool for removing a solid color background from footage.

#### 🖼️🎭 Image Selector by Index
*Category: `Automation/Image`*
Selects and loads a batch of images from a directory based on a corresponding batch of indices (numbers). A key node for creating emotion-driven character animations.

#### 🖼️ Get Last Image from Batch
*Category: `Automation/Image`*
A simple utility node that takes an image batch (e.g., a video timeline) and outputs only the very last frame as a new, single-image batch.
*   **Use Case**: Ideal for extracting a final frame from a generated video to use as a thumbnail.

### Automation/Publishing

#### 🚀 Webhook Uploader
*Category: `Automation/Publishing`*
Sends your final video, thumbnail, and description to a third-party automation service like **Make.com** or **Zapier** via a webhook. This is the recommended, secure, and flexible way to upload your content.

#### ☁️ S3 Uploader
*Category: `Automation/Publishing`*
Uploads a local file to an Amazon S3 bucket and makes it publicly accessible. This is a powerful way to host your media and get a public URL that can be used by other services, such as the `Webhook Uploader`.

### Automation/Video

#### 🎬 SRT Parser
*Category: `Automation/Video`*
Parses SRT (subtitle) formatted text to extract timing and content. Batch-compatible with a properly formatted `text_list` output.

#### 🎞️ SRT Scene Generator
*Category: `Automation/Video`*
Generates a timeline of blank frames based on a flat list of durations from the `SRT Parser`.

#### 🔂 Image Batch Repeater
*Category: `Automation/Video`*
The core assembly node for images. It takes a batch of content images and repeats each one according to a list of frame counts. Highly memory-optimized to pre-allocate one single block of memory.

#### 🔂 Mask Batch Repeater
*Category: `Automation/Video`*
The dedicated assembly node for masks. Uses the same memory-efficient logic as the `Image Batch Repeater`.

#### 🔊 Audio Reactive Paster
*Category: `Automation/Video`*
Pastes an overlay image/timeline onto a background video, with its position animated by the amplitude of an audio signal. Memory-efficient and includes advanced smoothing options.

### Automation/Time

#### 🕒 Time Scheduler
*Category: `Automation/Time`*
A utility node for calculating future dates and times, perfect for scheduling posts.
*   **Modes**: `Offset from Current Time` or `Next Specific Time`.
*   **Outputs**: A `formatted_date` (YYYY-MM-DD) and `formatted_time` (HH:MM).

### Automation/Utils

#### 🔧 Image/Mask Batch Combiner
*Category: `Automation/Utils`*
A crucial utility node that merges a sequence of individual images/masks (from an iterated node) into a single, unified batch.
*   **Use Case**: Place this node **after** an iterated node (like `Image Selector by Index`) to ensure the rest of your workflow runs only once.

#### 🔧 Image Batch Concatenator
*Category: `Automation/Utils`*
A memory-efficient node for combining multiple image batches (video clips) into a single, continuous timeline.
*   **How it works**: It has one required and multiple optional inputs. It pre-allocates memory and copies data slice by slice to avoid memory spikes.
*   **Use Case**: The perfect final step to join video chunks processed separately back together.

#### 🧹 Memory Purge
*Category: `Automation/Utils`*
A vital utility for managing system resources in very large workflows. Forces Python's garbage collector to run, freeing up the maximum amount of RAM and VRAM possible. It also reports how much memory was freed.
*   **Use Case**: Insert this node immediately before a memory-heavy node (like `Image Batch Repeater`) to prevent crashes and force a cache refresh.

#### 📜 Batch to String
*Category: `Automation/Utils`*
A utility node to convert a list/batch of strings into a single string with a custom separator.

#### 🔢 String to Integer
*Category: `Automation/Utils`*
Converts a string or a batch of strings into integers. Robust against messy LLM outputs.

#### 📜 String Literal to List Converter
*Category: `Automation/Converters`*
This node takes a string that is a Python list literal (e.g., `"['a', 'b', 'c']"`) and converts it into a proper ComfyUI batch/list output.

---

## Experimental Nodes

### Automation/Publishing (Direct) (Experimental)

**⚠️ Warning:** These nodes interact directly with TikTok's website by controlling a web browser. They are considered **experimental and fragile**. TikTok frequently changes its website code, which can break these nodes without warning. For reliable, long-term automation, the [**Webhook Uploader**](#-webhook-uploader) method is strongly recommended.

#### 🔥 Direct TikTok Uploader (Experimental)
*Category: `Automation/Publishing (Direct)`*
Uploads a video directly to TikTok. This node automates a browser to log in (using your cookie) and perform the upload.
*   **Requires**: A valid `sessionid` cookie from your TikTok account. You must install `tiktok-uploader` and `selenium` (see installation).
*   **"Fire-and-Forget"**: Due to the way TikTok processes uploads, this node initiates the post and then "fires and forgets," assuming success after a short wait.

#### 📅 Scheduled TikTok Uploader (Experimental)
*Category: `Automation/Publishing (Direct)`*
Schedules a video to be posted on TikTok at a future date and time. It uses the same browser automation method as the direct uploader.
*   **Requires**: Same requirements as the Direct TikTok Uploader.
*   **Use Case**: Combine with the `Time Scheduler` node to fully automate a content calendar.