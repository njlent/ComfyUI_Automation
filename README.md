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
    (Or, if you downloaded the files manually, just place the `ComfyUI_Automation` folder here).
3.  Restart ComfyUI. The ComfyUI-Manager (or the terminal) should detect the `requirements.txt` file and prompt you to install the necessary dependencies (`feedparser`, `requests`, `beautifulsoup4`, `Pillow`, `pandas`, `scipy`, `boto3`, `pytz`, `psutil`).
4.  If the dependencies are not installed automatically, you can install them manually by opening a terminal/command prompt, navigating to your ComfyUI installation, and running:
    ```bash
    pip install -r ComfyUI/custom_nodes/ComfyUI_Automation/requirements.txt
    ```
5.  **For Experimental TikTok Nodes (Optional):** If you wish to use the direct TikTok uploader nodes, you must also place the `tiktok_nodes.py` file in the `ComfyUI_Automation` folder and install additional dependencies. Run the following command in your terminal:
    ```bash
    pip install tiktok-uploader selenium
    ```
    **Note:** These nodes are experimental and may break if TikTok changes its website.
6.  Restart ComfyUI one more time after all dependencies are installed. Your new nodes will appear in the "Automation" category when you right-click the canvas.

---

## Node Reference

### Automation/RSS

#### 📰 RSS Feed Reader
*Category: `Automation/RSS`*

![RSS Feed Reader](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/RSS_Feed_Reader.jpg?raw=true)

Fetches and parses entries from one or more RSS feeds.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `links` | `STRING` | One or more RSS feed URLs, each on a new line. |
| **(Input)** `max_entries` | `INT` | The maximum number of entries to fetch from EACH feed in the list. |
| **(Input)** `skip_entries` | `INT` | Skips the first N entries from each feed. Useful for pagination. |
| **(Input)** `batch_source_1` | `COMBO` | Selects the content (`title`, `summary`, or `link`) for the `content_batch_1` output. |
| **(Input)** `batch_source_2` | `COMBO` | Selects the content (`title`, `summary`, or `link`) for the `content_batch_2` output. |
| **(Input)** `output_mode` | `COMBO` | `Batch Output`: Returns lists for all outputs. `Concatenated String`: Joins raw/formatted text into single strings. |
| **(Output)** `raw_output_batch` | `STRING` | A batch/list of the raw JSON data for each entry. |
| **(Output)** `formatted_text_batch`| `STRING` | A batch/list of cleaned-up, human-readable summaries of each entry. |
| **(Output)** `content_batch_1`| `STRING` | A batch/list of content selected by `batch_source_1`. |
| **(Output)** `content_batch_2`| `STRING` | A batch/list of content selected by `batch_source_2`. |

### Automation/Web

#### 🕸️ Simple Web Scraper
*Category: `Automation/Web`*

![Simple Web Scraper](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Simple_Web_Scraper.jpg?raw=true)

A basic scraper that grabs all text and all image links from one or more URLs.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `url` | `STRING` | A single URL or a batch/list of URLs to scrape. |
| **(Output)** `extracted_texts_batch`| `STRING` | A batch/list of all text content extracted from each URL. |
| **(Output)** `image_urls_batch`| `STRING` | A batch/list of all image URLs found on each page. |

#### 🎯 Targeted Web Scraper
*Category: `Automation/Web`*

![Targeted Web Scraper](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Targeted_Web_Scraper.jpg?raw=true)

A powerful scraper that gives you fine-grained control to extract content from specific parts of a web page using CSS selectors, while simultaneously removing unwanted content.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `url` | `STRING` | A single URL or a batch of URLs to scrape. |
| **(Input)** `selectors` | `STRING` | CSS selectors for the main content areas you want to extract. Use browser 'Inspect' tool. E.g., `.article-body, #main-content` |
| **(Input)** `ignore_selectors` | `STRING` | CSS selectors for content to completely remove before extraction. Each on a new line. E.g., `nav, footer, .ad-container` |
| **(Output)** `extracted_text_batch`| `STRING` | A batch of text extracted only from the elements matching `selectors`. |
| **(Output)** `image_urls_batch`| `STRING` | A batch of image URLs found only within the elements matching `selectors`. |

### Automation/Image

#### 🖼️ Load Image From URL
*Category: `Automation/Image`*

![Load Image From URL](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Load_Image_From_URL.jpg?raw=true)

Downloads one or more images from URLs and prepares them as a standard ComfyUI `IMAGE` batch.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `image_url` | `STRING` | A single image URL or a batch/list of URLs to download. |
| **(Input)** `resize_mode` | `COMBO` | How to handle images of different sizes. 'Don't Resize' is not batch-compatible. |
| **(Input)** `target_width` | `INT` | The width all images will be resized to (unless 'Don't Resize' is selected). |
| **(Input)** `target_height`| `INT` | The height all images will be resized to (unless 'Don't Resize' is selected). |
| **(Output)** `image` | `IMAGE` | The downloaded and processed image(s) as a standard batch. |
| **(Output)** `mask` | `MASK` | The transparency mask for each image (fully opaque if the original was not transparent). |

#### 🖼️ Layered Image Processor
*Category: `Automation/Image`*

![Layered Image Processor](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Layered_Image_Processor.jpg?raw=true)

Creates a layered image effect by placing a scaled version of an image on top of a blurred, full-screen version of the same image.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `image` | `IMAGE` | The source image or image batch to process. |
| **(Input)** `width` | `INT` | The final width of the output canvas. |
| **(Input)** `height` | `INT` | The final height of the output canvas. |
| **(Input)** `blur_radius` | `FLOAT` | The radius for the Gaussian blur on the background layer. |
| **(Input)** `resampling_method`| `COMBO` | The algorithm used for resizing images. LANCZOS is high quality. |
| **(Input)** `x_offset` | `INT` | Horizontal offset for the foreground image. |
| **(Input)** `y_offset` | `INT` | Vertical offset for the foreground image. |
| **(Output)** `image` | `IMAGE` | The final composited layered image batch. |

#### ✍️ Text on Image
*Category: `Automation/Image`*

![Text on Image](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Text_on_Image.jpg?raw=true)

A highly advanced node for drawing stylized static text onto an image. It is fully batch-aware and packed with professional features, including emoji support.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `image` | `IMAGE` | The image or image batch to draw on. |
| **(Input)** `text` | `STRING` | The text string or batch of strings to d Emojis are supported! |
| **(Input)** `font_name` | `COMBO` | The font file to use for regular text. |
| **(Input)** `font_size` | `INT` | Font size in pixels. |
| **(Input)** `font_color` | `STRING` | Text color in R, G, B format (e.g., `255, 255, 255`). |
| **(Input)** `wrap_width` | `INT` | Maximum width in pixels for text wrapping. Set to 0 to disable. |
| **(Input)** `line_height_multiplier` | `FLOAT` | Multiplier for line spacing (e.g., 1.2 is 120% line height). |
| **(Input)** `style` | `COMBO` | Choose a style: `None`, `Background Block`, `Drop Shadow`, or `Stroke`. |
| **(Input)** `style_color` | `STRING` | R,G,B,A format for the chosen style (e.g., `0, 0, 0, 128`). |
| **(Input)** `bg_padding` | `INT` | Padding for the `Background Block` style. |
| **(Input)** `shadow_offset` | `INT` | Pixel offset for the `Drop Shadow` style. |
| **(Input)** `stroke_width` | `INT` | Width of the text stroke for the `Stroke` style. |
| **(Input)** `x_position` | `INT` | Horizontal nudge from the aligned position. |
| **(Input)** `y_position` | `INT` | Vertical nudge from the aligned position. |
| **(Input)** `horizontal_align`| `COMBO` | Horizontal alignment anchor for the text block (`left`, `center`, `right`). |
| **(Input)** `vertical_align`| `COMBO` | Vertical alignment anchor for the text block (`top`, `center`, `bottom`). |
| **(Input)** `margin` | `INT` | Padding from the edge of the image for alignment. |
| **(Output)** `image` | `IMAGE` | The image batch with the text drawn on it. |

#### ✍️ Paste Text on Image Batch
*Category: `Automation/Image`*

![Paste Text on Image Batch](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Paste_Text_on_Image_Batch.jpg?raw=true)

A powerful compositing node that pastes formatted text onto a background image batch or video timeline. This node is timeline-aware.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `background_image` | `IMAGE` | The image batch or video timeline to paste the text onto. |
| **(Input)** `text` | `STRING` | The text string or batch/list of strings to display. |
| **(Input)** `font_name` | `COMBO` | The font file to use. |
| **(Input)** `font_size` | `INT` | The font size in pixels. |
| **(Input)** `font_color` | `STRING` | Text color in R, G, B, A format (e.g., `255, 255, 255, 255`). |
| **(Input)** `wrap_width` | `INT` | Maximum width in pixels for text wrapping. |
| **(Input)** `x_position` | `INT` | Final horizontal position of the text block. |
| **(Input)** `y_position` | `INT` | Final vertical position of the text block. |
| **(Input)** `horizontal_align`| `COMBO` | Horizontal alignment anchor (`left`, `center`, `right`). |
| **(Input)** `vertical_align`| `COMBO` | Vertical alignment anchor (`top`, `center`, `bottom`). |
| **(Input)** `margin` | `INT` | Padding from the edge of the image. |
| **(Input)** `text_durations`| `INT` (Optional) | A list of frame counts to control the duration of each text. If provided, the sum should match the background frame count. |
| **(Output)** `image` | `IMAGE` | The background image batch with the text pasted on it according to the specified timings. |

#### ✍️ Animate Text on Image
*Category: `Automation/Image`*

![Animate Text on Image](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Animate_Text_on_Image.jpg?raw=true)

A comprehensive motion graphics node for creating animated text on a video timeline. It handles batches of text with synchronized timing and features advanced styling.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `background_image` | `IMAGE` | The background video timeline to draw the animation on. |
| **(Input)** `text` | `STRING` | A single text block or a list of texts to animate in sequence. Emojis are supported! |
| **(Input)** `animation_type`| `COMBO` | Choose animation: `Typewriter (Character by Character)` or `Reveal (Word by Word)`. |
| **(Input)** `animation_duration` | `INT` | Duration of the typing/reveal effect for each text block. |
| **(Input)** `duration_unit`| `COMBO` | `Frames`: Fixed duration. `Percent of Text Duration`: Duration is a percentage of the text's total display time. |
| **(Input)** `text_durations`| `INT` (Optional) | A list of frame counts specifying how long each text block is displayed. Must be connected to work. |
| ... | ... | *Plus all standard text formatting inputs from the `Text on Image` node (font, color, style, alignment, etc.).* |
| **(Output)** `image` | `IMAGE` | The background image batch with the text animated on it. |

#### 🔧 Transform Paster (Static)
*Category: `Automation/Image`*

![Transform Paster (Static)](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Transform_Paster.jpg?raw=true)

A core compositing tool for **single images**. It takes a background image, an overlay image, and a mask, and provides precise controls for transforming the overlay before pasting.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `background_image` | `IMAGE` | The base image to paste onto. Only the first image in a batch is used. |
| **(Input)** `overlay_image` | `IMAGE` | The image to transform and paste. Only the first image in a batch is used. |
| **(Input)** `overlay_mask` | `MASK` | The mask for the overlay. Only the first mask in a batch is used. |
| **(Input)** `size` | `INT` | The target size (longest side) of the overlay image before pasting. |
| **(Input)** `rotation` | `FLOAT` | Rotation of the overlay in degrees. |
| **(Input)** `x_offset` | `INT` | Final horizontal position (from center) of the overlay. |
| **(Input)** `y_offset` | `INT` | Final vertical position (from center) of the overlay. |
| **(Input)** `interpolation` | `COMBO` | The resampling filter to use for resizing. `LANCZOS` is high quality. |
| **(Output)** `composited_image`| `IMAGE` | The final single composited image. |

#### 🔧 Transform Paster (Batch)
*Category: `Automation/Image`*

![Transform Paster (Batch)](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Transform_Paster_Batch.jpg?raw=true)

A powerful and memory-efficient node for compositing video timelines. It transforms and pastes an overlay batch onto a background batch with precise timing controls.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `background_image` | `IMAGE` | The base video timeline to paste onto. |
| **(Input)** `overlay_image` | `IMAGE` | The overlay video timeline to transform and paste. |
| **(Input)** `overlay_mask` | `MASK` | The mask or mask timeline for the overlay. |
| **(Input)** `alignment_mode`| `COMBO` | `Paste at Start`: Aligns the overlay with the start of the background. `Paste at End`: Aligns it with the end. |
| **(Input)** `start_frame_offset`| `INT` | An offset in frames from the chosen alignment point. |
| **(Input)** `size` | `INT` | The target size (longest side) of the overlay frames. |
| **(Input)** `rotation` | `FLOAT` | Rotation of the overlay frames in degrees. |
| **(Input)** `x_offset` | `INT` | Final horizontal position (from center) of the overlay. |
| **(Input)** `y_offset` | `INT` | Final vertical position (from center) of the overlay. |
| **(Input)** `interpolation` | `COMBO` | The resampling filter to use for resizing. |
| **(Output)** `composited_image`| `IMAGE` | The final composited video timeline. |

#### ✨ Gaussian Blur
*Category: `Automation/Image`*

![Gaussian Blur](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Gaussian_Blur.jpg?raw=true)

A simple and efficient node to apply a Gaussian blur effect to an image or a batch of images.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `image` | `IMAGE` | The image or image batch to apply the blur to. |
| **(Input)** `radius` | `FLOAT` | The radius of the Gaussian blur. Higher values create a stronger blur. |
| **(Output)** `image` | `IMAGE` | The blurred image batch. |

#### ✨ Animate Gaussian Blur
*Category: `Automation/Image`*

![Animate Gaussian Blur](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Animate_Gaussian_Blur.jpg?raw=true)

Applies a Gaussian blur to a video timeline, with the blur strength animating smoothly from `0` to a `max_radius` over the duration of the clip.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `image` | `IMAGE` | The image batch (video timeline) to apply the animated blur to. |
| **(Input)** `max_radius` | `FLOAT` | The maximum blur strength, reached at the last frame of the batch. |
| **(Output)** `image` | `IMAGE` | The image batch with the blur animated over time. |

#### 🟩 Green Screen Keyer
*Category: `Automation/Image`*

![Green Screen Keyer](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Green_Screen_Keyer.jpg?raw=true)

A node for performing chroma keying on an image or video timeline.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `image` | `IMAGE` | The image batch with the solid color background to key out. |
| **(Input)** `key_color` | `STRING` | The RGB color to key out (e.g., `0, 255, 0` for pure green). |
| **(Input)** `threshold` | `FLOAT` | The tolerance for the key. Higher values include more color variations. |
| **(Input)** `softness` | `FLOAT` | The falloff or feathering of the mask's edge for a smoother transition. |
| **(Input)** `invert_mask`| `BOOLEAN` | If `Yes`, the keyed color will be white in the mask instead of black. |
| **(Output)** `image_out` | `IMAGE` | A passthrough of the original input image batch. |
| **(Output)** `mask` | `MASK` | The generated alpha mask batch. |

#### 🖼️ Image Selector by Index
*Category: `Automation/Image`*

![Image Selector by Index](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Image_Selector_by_Index.jpg?raw=true)

Selects and loads a batch of images from a directory based on a corresponding batch of indices (numbers).

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `index_batch` | `INT` | A single integer or a batch/list of integers to select images with. |
| **(Input)** `directory_path`| `STRING` | The path to the directory containing the images. |
| **(Input)** `file_pattern`| `STRING` | A pattern for the filenames, using `{}` as a placeholder for the index (e.g., `face_{}.png`). |
| **(Input)** `fallback_image`| `IMAGE` (Optional) | An image to use if a specified index does not correspond to a file. |
| **(Output)** `image_batch` | `IMAGE` | A batch of the selected images. |
| **(Output)** `mask_batch` | `MASK` | A batch of the corresponding masks for the selected images. |

#### 🖼️ Get Last Image from Batch
*Category: `Automation/Image`*

![Get Last Image from Batch](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Get_Last_Image_from_Batch.jpg?raw=true)

A simple utility node that takes an image batch (e.g., a video timeline) and outputs only the very last frame as a new, single-image batch.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `image_batch` | `IMAGE` | The batch of images (e.g., a video timeline) to get the last frame from. |
| **(Output)** `last_image` | `IMAGE` | A new batch containing only the last frame of the input. |

### Automation/Publishing

#### 🚀 Webhook Uploader
*Category: `Automation/Publishing`*

![Webhook Uploader](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Webhook_Uploader.jpg?raw=true)

Sends your final video URL, thumbnail URL, and description to a third-party automation service like **Make.com** or **Zapier** via a webhook.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `webhook_url`| `STRING` | The unique webhook URL from your automation service. |
| **(Input)** `video_url` | `STRING` | The public URL of the video to be posted (e.g., from an S3 Uploader node). |
| **(Input)** `description`| `STRING` | The description/caption for the video. |
| **(Input)** `thumbnail_url`| `STRING` (Optional) | The public URL of the thumbnail image. |
| **(Input)** `any_string_1`| `STRING` (Optional) | An extra text field you can use in your automation. |
| **(Input)** `any_string_2`| `STRING` (Optional) | Another extra text field. |
| **(Output)** `response_text`| `STRING` | The text response from the webhook server, including status code. |

#### ☁️ S3 Uploader
*Category: `Automation/Publishing`*

![S3 Uploader](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/S3_Uploader.jpg?raw=true)

Uploads a local file to an Amazon S3 bucket and makes it publicly accessible.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `file_path` | `STRING` | The local path of the file (video, image, etc.) to upload. |
| **(Input)** `bucket_name`| `STRING` | The name of your Amazon S3 bucket. |
| **(Input)** `aws_access_key_id`| `STRING` | Your AWS Access Key ID. |
| **(Input)** `aws_secret_access_key`| `STRING` | Your AWS Secret Access Key. Treat this like a password. |
| **(Input)** `aws_region` | `STRING` | The AWS region your bucket is in (e.g., 'us-west-2', 'eu-central-1'). |
| **(Input)** `object_name`| `STRING` (Optional) | The desired name for the file in the bucket (e.g., 'videos/my_vid.mp4'). If empty, the original filename is used. |
| **(Output)** `public_url` | `STRING` | The publicly accessible URL of the uploaded file. |

### Automation/Video

#### 🎬 SRT Parser
*Category: `Automation/Video`*

![SRT Parser](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/SRT_Parser.jpg?raw=true)

Parses SRT (subtitle) formatted text to extract timing and content.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `srt_content`| `STRING` | Paste the entire content of your SRT file here. |
| **(Input)** `handle_pauses`| `COMBO` | `Include Pauses`: Creates empty entries for silent gaps. `Ignore Pauses`: Skips gaps. |
| **(Output)** `text_batch` | `STRING` | *Legacy Output*. A batch of subtitle text strings. Use `text_list` for better compatibility. |
| **(Output)** `start_ms_batch` | `INT` | A batch of start times for each entry in milliseconds. |
| **(Output)** `end_ms_batch` | `INT` | A batch of end times for each entry in milliseconds. |
| **(Output)** `duration_ms_batch`| `INT` | A batch of durations for each entry in milliseconds. |
| **(Output)** `section_count`| `INT` | The total number of sections (lines + pauses) found. |
| **(Output)** `text_list` | `LIST` | A properly formatted list of subtitle text strings, compatible with iterating nodes. |

#### 🎞️ SRT Scene Generator
*Category: `Automation/Video`*

![SRT Scene Generator](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/SRT_Scene_Generator.jpg?raw=true)

Generates a timeline of blank frames based on a flat list of durations from the `SRT Parser`.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `duration_ms_batch`| `INT` | Connect the 'duration_ms_batch' from an SRT Parser here. |
| **(Input)** `fps` | `INT` | Frames per second for the output video timeline. |
| **(Input)** `width` | `INT` | Width of the video frames. |
| **(Input)** `height` | `INT` | Height of the video frames. |
| **(Output)** `image_timeline` | `IMAGE` | A batch of black frames representing the full video duration. |
| **(Output)** `start_frame_indices`| `INT` | A batch of starting frame numbers for each scene. |
| **(Output)** `frame_counts` | `INT` | A batch of frame counts (durations) for each scene. |

#### 🔂 Image Batch Repeater
*Category: `Automation/Video`*

![Image Batch Repeater](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Image_Batch_Repeater.jpg?raw=true)

The core assembly node for images. It takes a batch of content images and repeats each one according to a list of frame counts. Highly memory-optimized.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `image` | `IMAGE` | The image or batch of images to repeat. |
| **(Input)** `repeat_counts`| `INT` | An integer or a list of integers (like 'frame_counts' from SRT Scene Generator) specifying how many times to repeat each image. |
| **(Output)** `image_timeline` | `IMAGE` | The final assembled video timeline. |

#### 🔂 Mask Batch Repeater
*Category: `Automation/Video`*

![Mask Batch Repeater](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Mask_Batch_Repeater.jpg?raw=true)

The dedicated assembly node for masks. It takes a batch of masks and repeats them according to a list of frame counts.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `mask` | `MASK` | The mask or batch of masks to repeat. |
| **(Input)** `repeat_counts`| `INT` | An integer or a list of integers specifying how many times to repeat each mask. |
| **(Output)** `mask_timeline` | `MASK` | The final assembled mask timeline. |

#### 🔊 Audio Reactive Paster
*Category: `Automation/Video`*

![Audio Reactive Paster](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Audio_Reactive_Paster.jpg?raw=true)

Pastes an overlay image/timeline onto a background video, with its position animated by the amplitude of an audio signal.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `background_image` | `IMAGE` | The base video or image batch to paste onto. |
| **(Input)** `overlay_image` | `IMAGE` | The image or timeline of images to paste. |
| **(Input)** `overlay_mask` | `MASK` | The mask or timeline of masks for the overlay. |
| **(Input)** `audio` | `AUDIO` | The single audio signal to drive the animation for the entire timeline. |
| **(Input)** `fps` | `INT` | Must match the FPS of your background video timeline. |
| **(Input)** `size` | `INT` | The target size (longest side) of the overlay image. |
| **(Input)** `x_strength` | `FLOAT` | Multiplier for horizontal movement based on audio amplitude. |
| **(Input)** `y_strength` | `FLOAT` | Multiplier for vertical movement based on audio amplitude. |
| **(Input)** `smoothing_method`| `COMBO` | The algorithm (`Gaussian`, `EMA`, `SMA`) to smooth the animation. |
| ... | ... | *Plus other inputs for alignment, offsets, and smoothing parameters.* |
| **(Output)** `image_timeline` | `IMAGE` | The composited video timeline with the audio-reactive overlay. |
| **(Output)** `amplitude_visualization`| `IMAGE` | A simple graph visualizing the smoothed audio amplitude over time. |

### Automation/Time

#### 🕒 Time Scheduler
*Category: `Automation/Time`*

![Time Scheduler](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Time_Scheduler.jpg?raw=true)

A utility node for calculating future dates and times, perfect for scheduling posts.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `mode` | `COMBO` | `Offset from Current Time`: schedule relative to now. `Next Specific Time`: schedule for the next occurrence of a fixed time. |
| **(Input)** `utc_timezone` | `STRING` | The target timezone (e.g., 'America/New_York', 'Europe/London'). |
| **(Input)** `offset_days`| `INT` (Optional) | Days to offset from the current time (for 'Offset' mode). |
| **(Input)** `offset_hours`| `INT` (Optional) | Hours to offset from the current time (for 'Offset' mode). |
| **(Input)** `offset_minutes`| `INT` (Optional) | Minutes to offset from the current time (for 'Offset' mode). |
| **(Input)** `specific_time`| `STRING` (Optional) | The specific time in HH:MM format (for 'Next Specific Time' mode). |
| **(Output)** `formatted_date`| `STRING` | The calculated date in YYYY-MM-DD format. |
| **(Output)** `formatted_time`| `STRING` | The calculated time in HH:MM (24-hour) format. |

### Automation/Utils

#### 🔢 String to Integer
*Category: `Automation/Utils`*

![String to Integer](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/String_to_Integer.jpg?raw=true)

Converts a string or a batch of strings into integers. Robust against messy LLM outputs, as it finds the first available number in the text.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `text` | `STRING` | The string or batch of strings to convert. |
| **(Output)** `int_output`| `INT` | The resulting integer or batch of integers. |

#### 📜 Batch to String
*Category: `Automation/Utils`*

![Batch to String](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Batch_to_String.jpg?raw=true)

A utility node to convert a list/batch of strings into a single string with a custom separator.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `string_batch`| `STRING` | The batch/list of strings to join. |
| **(Input)** `separator` | `STRING` | The characters to place between each string (e.g., `\n\n` for double newline). |
| **(Output)** `string` | `STRING` | The final concatenated string. |

#### 📜 String Literal to List Converter
*Category: `Automation/Converters`*

![String Literal to List Converter](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/String_Literal_to_List_Converter.jpg?raw=true)

This node takes a string that is a Python list literal (e.g., `"['a', 'b', 'c']"`) and converts it into a proper ComfyUI batch/list output.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `string_literal`| `STRING` | The string formatted as a Python list literal. |
| **(Output)** `STRING_LIST`| `LIST` | A proper ComfyUI list/batch that can be used by iterating nodes. |

#### 🔧 Image/Mask Batch Combiner
*Category: `Automation/Utils`*

![Image/Mask Batch Combiner](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Image_Mask_Batch_Combiner.jpg?raw=true)

A crucial utility node that merges a sequence of individual images/masks (from an iterated node) into a single, unified batch. Place this **after** an iterated node to "break" the iteration.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `image_batch`| `IMAGE` (List) | A sequence of single-frame image batches from an iterated node. |
| **(Input)** `mask_batch` | `MASK` (List) | A sequence of single-frame mask batches from an iterated node. |
| **(Output)** `combined_image_batch`| `IMAGE` | A single, unified image batch containing all input frames. |
| **(Output)** `combined_mask_batch`| `MASK` | A single, unified mask batch containing all input masks. |

#### 🔧 Image Batch Concatenator
*Category: `Automation/Utils`*

![Image Batch Concatenator](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Image_Batch_Concatenator.jpg?raw=true)

A memory-efficient node for combining multiple image batches (video clips) into a single, continuous timeline.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `image_batch_1`| `IMAGE` | The first image batch. This one is required. |
| **(Input)** `image_batch_2`| `IMAGE` (Optional) | An optional second image batch. |
| **(Input)** `image_batch_3`| `IMAGE` (Optional) | An optional third image batch. |
| **(Input)** `image_batch_4`| `IMAGE` (Optional) | An optional fourth image batch. |
| **(Input)** `image_batch_5`| `IMAGE` (Optional) | An optional fifth image batch. |
| **(Output)** `combined_image_batch`| `IMAGE` | The final, single, continuous video timeline. |

#### 🧹 Memory Purge
*Category: `Automation/Utils`*

![Memory Purge](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Memory_Purge.jpg?raw=true)

A vital utility for managing system resources in very large workflows. It forces garbage collection and empties the CUDA cache, freeing up RAM and VRAM.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `image` | `IMAGE` | A passthrough input to enforce execution order. The image is not modified. |
| **(Output)** `image_passthrough`| `IMAGE` | The same, unmodified image that was passed in. |

---

## Experimental Nodes

### Automation/Publishing (Direct) (Experimental)

**⚠️ Warning:** These nodes interact directly with TikTok's website by controlling a web browser in the background. They are considered **experimental and fragile**. TikTok frequently changes its website code, which can break these nodes without warning. For reliable, long-term automation, the [**Webhook Uploader**](#-webhook-uploader) method is strongly recommended.

#### 🔥 Direct TikTok Uploader (Experimental)
*Category: `Automation/Publishing (Direct)`*

![Direct TikTok Uploader](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Direct_TikTok_Uploader.jpg?raw=true)

Uploads a video directly to TikTok. This node automates a browser to log in (using your cookie) and perform the upload.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `video_path`| `STRING` | The local path to the video file to be uploaded. |
| **(Input)** `description`| `STRING` | The video caption/description. |
| **(Input)** `sessionid_cookie`| `STRING` | Your valid `sessionid_ss` cookie from a logged-in TikTok browser session. |
| **(Input)** `wait_after_post`| `INT` | Seconds to wait after clicking 'Post' before assuming success. The video uploads in the background. |
| **(Input)** `chrome_executable_path`| `STRING` (Optional)| Full path to your `chrome.exe` or `chromium` executable if it's not found automatically. |
| **(Input)** `comment_permission`| `BOOLEAN` (Optional)| Allow users to comment on the video. |
| **(Input)** `duet_permission`| `BOOLEAN` (Optional)| Allow users to Duet this video. |
| **(Input)** `stitch_permission`| `BOOLEAN` (Optional)| Allow users to Stitch this video. |
| **(Output)** `upload_status`| `STRING` | A message indicating the success ("Fire-and-Forget") or failure of the upload attempt. |

#### 📅 Scheduled TikTok Uploader (Experimental)
*Category: `Automation/Publishing (Direct)`*

![Scheduled TikTok Uploader](https://github.com/njlent/ComfyUI_Automation/blob/main/readme/Scheduled_TikTok_Uploader.jpg?raw=true)

Schedules a video to be posted on TikTok at a future date and time. It uses the same browser automation method as the direct uploader.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **(Input)** `video_path`| `STRING` | The local path to the video file to be uploaded. |
| **(Input)** `description`| `STRING` | The video caption/description. |
| **(Input)** `sessionid_cookie`| `STRING` | Your valid `sessionid_ss` cookie from a logged-in TikTok browser session. |
| **(Input)** `schedule_date`| `STRING` | Date to schedule the post, in `YYYY-MM-DD` format. |
| **(Input)** `schedule_time`| `STRING` | Time to schedule the post, in 24-hour `HH:MM` format. |
| **(Input)** `wait_after_post`| `INT` | Seconds to wait after clicking 'Schedule' before assuming success. |
| **(Input)** `chrome_executable_path`| `STRING` (Optional)| Full path to your `chrome.exe` or `chromium` executable if it's not found automatically. |
| **(Input)** `comment_permission`| `BOOLEAN` (Optional)| Allow users to comment on the video. |
| **(Input)** `duet_permission`| `BOOLEAN` (Optional)| Allow users to Duet this video. |
| **(Input)** `stitch_permission`| `BOOLEAN` (Optional)| Allow users to Stitch this video. |
| **(Output)** `upload_status`| `STRING` | A message indicating the success ("Fire-and-Forget") or failure of the scheduling attempt. |