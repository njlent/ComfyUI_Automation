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
*   [**Transform Paster**](#-transform-paster)
*   [**Gaussian Blur**](#-gaussian-blur)
*   [**Webhook Uploader**](#-webhook-uploader)
*   [**S3 Uploader**](#-s3-uploader)
*   [**SRT Parser**](#-srt-parser)
*   [**SRT Scene Generator**](#️-srt-scene-generator)
*   [**Image Batch Repeater**](#-image-batch-repeater)
*   [**Mask Batch Repeater**](#-mask-batch-repeater)
*   [**Audio Reactive Paster**](#-audio-reactive-paster)
*   [**Image Selector by Index**](#️-image-selector-by-index)
*   [**Time Scheduler**](#-time-scheduler)
*   [**String to Integer**](#-string-to-integer)
*   [**Batch to String**](#-batch-to-string)
*   [**String Literal to List Converter**](#-string-literal-to-list-converter)
*   [**Image/Mask Batch Combiner**](#-imagemask-batch-combiner)
*   [**Memory Purge**](#-memory-purge)
*   [**Direct TikTok Uploader**](#-direct-tiktok-uploader-experimental)
*   [**Scheduled TikTok Uploader**](#-scheduled-tiktok-uploader-experimental)

---

## Installation

1.  Navigate to your `ComfyUI/custom_nodes/` directory.
2.  Clone this repository into that directory:
    ```bash
    git clone https://github.com/njlent/ComfyUI_Automation ComfyUI_Automation
    ```
    (Or, if you downloaded the files manually, just place the `ComfyUI_Automation` folder here).
3.  Restart ComfyUI. The ComfyUI-Manager (or the terminal) should detect the `requirements.txt` file and prompt you to install the necessary dependencies (`feedparser`, `requests`, `beautifulsoup4`, `Pillow`, `torchaudio`, `pandas`, `scipy`, `boto3`, `pytz`).
4.  If the dependencies are not installed automatically, you can install them manually by opening a terminal/command prompt, navigating to your ComfyUI installation, and running:
    ```bash
    pip install -r ComfyUI/custom_nodes/ComfyUI_Automation/requirements.txt
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
    *   A class `postTitle` becomes the selector `.postTitle`.
    *   An ID `main-article` becomes the selector `#main-article`.
    *   A tag `article` is just `article`.
*   **Use Case**: You want to scrape the main text of a news article. You set `selectors` to `.article-body`. But the article has annoying "Related Posts" links inside it in a `div` with `class="related-links"`. You add `.related-links` to the `ignore_selectors` input to remove them before the main text is extracted.

### Automation/Image

#### 🖼️ Load Image From URL
*Category: `Automation/Image`*
Downloads one or more images from URLs and prepares them as a standard ComfyUI `IMAGE` batch.

#### 🖼️ Layered Image Processor
*Category: `Automation/Image`*
Creates a layered image effect by placing a scaled version of an image on top of a blurred, full-screen version of the same image. It correctly handles both upscaling and downscaling to ensure the foreground image always fits the canvas dimensions. Fully batch-aware.
*   **Features**: Includes `x_offset` and `y_offset` inputs to precisely position the foreground layer off-center.

#### ✍️ Text on Image
*Category: `Automation/Image`*
A highly advanced node for drawing stylized static text onto an image. It is fully batch-aware and packed with professional features.
*   **Emoji Support**: Automatically detects and renders emojis using your system's native emoji font.
*   **Formatting**: Full control over font, size, color, alignment, and positioning.
*   **Word Wrap**: `wrap_width` input for automatic word wrapping.
*   **Line Height**: `line_height_multiplier` for precise control over spacing between lines.
*   **Styling**:
    *   `style`: Choose `None`, `Background Block`, `Drop Shadow`, or `Stroke`.
    *   **Per-Line Background Block**: The background is drawn tightly around each individual line of wrapped text for a clean, modern look.
    *   Full controls for style color, padding, shadow offset, and stroke width.

#### ✍️ Paste Text on Image Batch
*Category: `Automation/Image`*
A powerful compositing node that pastes formatted text onto a background image batch or video timeline. This node is timeline-aware.
*   **Inputs**:
    *   `background_image`: The video timeline to draw on.
    *   `text`: A list of strings to display.
    *   `text_durations` (Optional): A list of frame counts (e.g., from `SRT Scene Generator`) to control the display duration for each corresponding text in the list.
    *   `wrap_width`: Automatic word wrapping for long text.

#### ✍️ Animate Text on Image
*Category: `Automation/Image`*
A comprehensive motion graphics node for creating animated text on a video timeline. It handles batches of text with synchronized timing and features the same advanced styling as the `Text on Image` node.
*   **Animation**:
    *   `animation_type`: Choose between `Typewriter` (character-by-character) or `Reveal` (word-by-word).
    *   `animation_duration` & `duration_unit`: Precisely control the animation speed in `Frames` or as a `Percent of Text Duration`.
*   **Timeline Control**:
    *   Takes a `text` list and an optional `text_durations` list to animate multiple text blocks in sequence over a video.
*   **Advanced Styling**: Includes all the features of the static `Text on Image` node, such as per-line background blocks, drop shadows, and strokes.
*   **Memory Efficient**: Designed to handle long, high-resolution videos without running out of RAM.

#### 🔧 Transform Paster
*Category: `Automation/Image`*
A core compositing tool for single images. It takes a background image, an overlay image, and a mask, and provides precise controls for transforming the overlay before pasting.
*   **Controls**: Full control over `size` (upscaling and downscaling), `rotation`, and final `x_offset`/`y_offset` position.
*   **Use Case**: Perfect for creating static compositions or preparing elements before they are used in a larger batch or video workflow.

#### ✨ Gaussian Blur
*Category: `Automation/Image`*
A simple and efficient node to apply a Gaussian blur effect to an image or a batch of images.
*   **Inputs**:
    *   `image`: The image or image batch to be blurred.
    *   `radius`: A float value to control the strength of the blur effect.
*   **Output**: A new `IMAGE` batch with the blur applied to every frame.

#### 🖼️🎭 Image Selector by Index
*Category: `Automation/Image`*
Selects and loads a batch of images from a directory based on a corresponding batch of indices (numbers). A key node for creating emotion-driven character animations.

### Automation/Publishing

#### 🚀 Webhook Uploader
*Category: `Automation/Publishing`*
Sends your final video, thumbnail, and description to a third-party automation service like **Make.com** or **Zapier** via a webhook. This is the recommended, secure, and flexible way to upload your content to platforms like TikTok, YouTube, Instagram, etc.

*   **How it Works**:
    1.  Create an automation in a service like Make.com that starts with a "Webhook" trigger. This will give you a unique URL.
    2.  In ComfyUI, after your video is saved, connect its `file_path` (from a Save Video node), your description, and an optional thumbnail path to this node.
    3.  Paste the webhook URL from your automation service into the node.
    4.  When your workflow runs, this node sends all the data to your automation service, which then handles the secure login and posting to TikTok.
*   **Inputs**:
    *   `webhook_url`: The secret URL from your automation service.
    *   `video_path`: The path to the final video file.
    *   `description`: The text caption for your post.
    *   `thumbnail_path` (Optional): The path to a thumbnail image.
    *   `any_string_1/2` (Optional): Extra text fields for more advanced automations.
*   **Output**: The response from the webhook server for debugging.

#### ☁️ S3 Uploader
*Category: `Automation/Publishing`*
Uploads a local file (like a video or thumbnail) to an Amazon S3 bucket and makes it publicly accessible. This is a powerful way to host your media and get a public URL that can be used by other services, such as the `Webhook Uploader`.
*   **Inputs**:
    *   `file_path`: The local path to the file you want to upload.
    *   `bucket_name`: Your S3 bucket's name.
    *   `aws_access_key_id` / `aws_secret_access_key`: Your AWS credentials. **Treat these like passwords and do not share them.**
    *   `aws_region`: The region your bucket is located in (e.g., `us-east-1`).
    *   `object_name` (Optional): The desired filename in the bucket.
*   **Output**: The public URL of the uploaded file (e.g., `https://my-bucket.s3.us-east-1.amazonaws.com/my-video.mp4`).

### Automation/Video

#### 🎬 SRT Parser
*Category: `Automation/Video`*
Parses SRT (subtitle) formatted text to extract timing and content. Batch-compatible with a properly formatted `text_list` output.

#### 🎞️ SRT Scene Generator
*Category: `Automation/Video`*
Generates a timeline of blank frames based on a flat list of durations from the `SRT Parser`.

#### 🔂 Image Batch Repeater
*Category: `Automation/Video`*
The core assembly node for images. It takes a batch of content images and repeats each one according to a list of frame counts from `SRT Scene Generator`. This node is heavily memory-optimized to pre-allocate one single block of memory, allowing for the creation of very long video timelines without crashing.

#### 🔂 Mask Batch Repeater
*Category: `Automation/Video`*
The dedicated assembly node for masks. Use this in parallel with the `Image Batch Repeater` to create a synchronized mask timeline. This node uses the same memory-efficient logic as the `Image Batch Repeater`.

#### 🔊 Audio Reactive Paster
*Category: `Automation/Video`*
Pastes an overlay image (or an image timeline) onto a background video, with its position animated by the amplitude of an audio signal.
*   **Features**:
    *   Handles both single overlay images and full video timelines as overlays.
    *   Allows for upscaling and downscaling of the overlay image.
    *   Advanced smoothing methods (`Gaussian`, `EMA`, `SMA`) for high-quality motion.
    *   Memory efficient design to handle long videos without crashing.

### Automation/Time

#### 🕒 Time Scheduler
*Category: `Automation/Time`*
A utility node for calculating future dates and times, perfect for scheduling posts.
*   **Modes**:
    *   `Offset from Current Time`: Calculates a future time by adding days, hours, and minutes to the current time.
    *   `Next Specific Time`: Finds the next occurrence of a specific time (e.g., `08:30`). If the time has already passed today, it schedules for tomorrow.
*   **Inputs**: A valid timezone (e.g., `America/New_York`, `Europe/London`), and the required offsets or specific time.
*   **Outputs**: A `formatted_date` (YYYY-MM-DD) and `formatted_time` (HH:MM) string, ready to be used by the `Scheduled TikTok Uploader`.

### Automation/Utils

#### 🔧 Image/Mask Batch Combiner
*Category: `Automation/Utils`*
A crucial utility node that solves a common ComfyUI batching problem. It takes a sequence of individual images/masks (often from an iterated node like `Image Selector by Index`) and merges them into a single, unified batch.
*   **Use Case**: Place this node **directly after** `Image Selector by Index` and before `Image Batch Repeater` to ensure the rest of your workflow runs only once, producing a single video instead of multiple separate ones.

#### 🧹 Memory Purge
*Category: `Automation/Utils`*
A vital utility for managing system resources in very large workflows. This node forces Python's garbage collector to run and clears PyTorch's CUDA cache, freeing up the maximum amount of RAM and VRAM possible.
*   **Why it's needed**: In a long workflow, previous nodes can leave large amounts of data (like image batches) in memory. This can cause memory allocation errors on resource-heavy nodes, even if you have a lot of RAM.
*   **How to use**: Insert this node immediately before a node that requires a large amount of memory, such as `Image Batch Repeater`. It acts as a simple passthrough and will not alter the data.
*   **Example Workflow**: `[Some Node] -> [🧹 Memory Purge] -> [🔂 Image Batch Repeater]`

#### 📜 Batch to String
*Category: `Automation/Utils`*
A utility node to convert a list/batch of strings into a single string with a custom separator.

#### 🔢 String to Integer
*Category. `Automation/Utils`*
Converts a string or a batch of strings into integers. It's robust against messy LLM outputs by finding the first number within the text.

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
*   **"Fire-and-Forget"**: Due to the way TikTok processes uploads, this node initiates the post and then "fires and forgets," assuming success after a short wait. It does not wait for full processing confirmation.

#### 📅 Scheduled TikTok Uploader (Experimental)
*Category: `Automation/Publishing (Direct)`*
Schedules a video to be posted on TikTok at a future date and time. It uses the same browser automation method as the direct uploader.
*   **Requires**: Same requirements as the Direct TikTok Uploader.
*   **Use Case**: Combine with the `Time Scheduler` node to fully automate a content calendar.