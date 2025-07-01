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
*   [**SRT Parser**](#-srt-parser)
*   [**SRT Scene Generator**](#️-srt-scene-generator)
*   [**Image Batch Repeater**](#-image-batch-repeater)
*   [**Mask Batch Repeater**](#-mask-batch-repeater)
*   [**Audio Reactive Paster**](#-audio-reactive-paster)
*   [**Image Selector by Index**](#️-image-selector-by-index)
*   [**String to Integer**](#-string-to-integer)
*   [**Batch to String**](#-batch-to-string)
*   [**String Literal to List Converter**](#-string-literal-to-list-converter)
*   [**Image/Mask Batch Combiner**](#-imagemask-batch-combiner)

---

## Installation

1.  Navigate to your `ComfyUI/custom_nodes/` directory.
2.  Clone this repository into that directory:
    ```bash
    git clone https://github.com/nj-lent/njlent-comfyui_automation.git ComfyUI_Automation
    ```
    (Or, if you downloaded the files manually, just place the `ComfyUI_Automation` folder here).
3.  Restart ComfyUI. The ComfyUI-Manager (or the terminal) should detect the `requirements.txt` file and prompt you to install the necessary dependencies (`feedparser`, `requests`, `beautifulsoup4`, `Pillow`, `torchaudio`, `pandas`, `scipy`).
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

### Automation/Web

#### 🕸️ Simple Web Scraper
*Category: `Automation/Web`*
A basic scraper that grabs all text and all image links from one or more URLs.

#### 🎯 Targeted Web Scraper
*Category: `Automation/Web`*
A powerful scraper that extracts content from specific parts of a page using CSS selectors, with the ability to ignore unwanted elements.

### Automation/Image

#### 🖼️ Load Image From URL
*Category: `Automation/Image`*
Downloads one or more images from URLs and prepares them as a standard ComfyUI `IMAGE` batch.

#### 🖼️ Layered Image Processor
*Category: `Automation/Image`*
Creates a layered image effect by placing a scaled version of an image on top of a blurred, full-screen version of the same image. Fully batch-aware.
*   **New Features**: Includes `x_offset` and `y_offset` inputs to precisely position the foreground layer off-center for more creative compositions.

#### ✍️ Text on Image
*Category: `Automation/Image`*
Draws text directly onto an image with various formatting options. Intelligently handles batches of images and/or text.
*   **New Features**: Supports automatic `wrap_width` for word wrapping long text blocks. The font dropdown is now populated with fonts available on your system.

#### ✍️ Paste Text on Image Batch
*Category: `Automation/Image`*
A powerful compositing node that pastes formatted text onto a background image batch or video timeline. This node is timeline-aware.
*   **Inputs**:
    *   `background_image`: The video timeline to draw on.
    *   `text`: A list of strings to display.
    *   `text_durations` (Optional): A list of frame counts (e.g., from `SRT Scene Generator`) to control the display duration for each corresponding text in the list.
    *   `wrap_width`: Automatic word wrapping for long text.
    *   Full alignment, positioning, and font controls.

#### ✍️ Animate Text on Image
*Category: `Automation/Image`*
A comprehensive motion graphics node for creating animated text on a video timeline. It can handle batches of text with synchronized timing and features advanced styling options for professional results.
*   **Animation**:
    *   `animation_type`: Choose between `Typewriter` (character-by-character) or `Reveal` (word-by-word).
    *   `animation_duration` & `duration_unit`: Precisely control the animation speed in `Frames` or as a `Percent of Text Duration`.
*   **Timeline Control**:
    *   Takes a `text` list and an optional `text_durations` list to animate multiple text blocks in sequence over a video.
*   **Styling**:
    *   `style`: Choose `None`, `Background Block`, or `Drop Shadow`.
    *   **Per-Line Background Block**: The background block is intelligently drawn around each line of wrapped text individually, preventing ugly empty corners.
    *   Full controls for style color, padding, shadow offset, and blur.
*   **Memory Efficient**: Designed to handle long, high-resolution videos without running out of RAM.

#### 🖼️🎭 Image Selector by Index
*Category: `Automation/Image`*
Selects and loads a batch of images from a directory based on a corresponding batch of indices (numbers). This is a key node for creating emotion-driven character animations.
*   **Inputs**:
    *   `index_batch`: A list of integers (e.g., from an LLM via `String to Integer`) used to select the images.
    *   `directory_path`: The path to the folder containing your numbered image assets.
    *   `file_pattern`: The naming pattern for your files. Use `{}` as a placeholder for the index number (e.g., `face_{}.png`).
    *   `fallback_image` (Optional): An image to use if a numbered file is not found, preventing errors.
*   **Outputs**:
    *   `image_batch`: The batch of selected images, resized to be compatible.
    *   `mask_batch`: The corresponding masks for the selected images.

### Automation/Video

#### 🎬 SRT Parser
*Category: `Automation/Video`*
Parses SRT (subtitle) formatted text to extract timing and content. This node is batch-compatible and includes a properly formatted `text_list` output for easy integration with other nodes.

#### 🎞️ SRT Scene Generator
*Category: `Automation/Video`*
Generates a timeline of blank frames based on a flat list of durations from the `SRT Parser`.
*   **Outputs**:
    *   `image_timeline`: A single, long batch of blank frames representing the entire video duration.
    *   `start_frame_indices`, `frame_counts`: Critical timing data for assembling your video content.

#### 🔂 Image Batch Repeater
*Category: `Automation/Video`*
The core assembly node for images. It takes a batch of content images and repeats each one according to a list of frame counts from `SRT Scene Generator`.

#### 🔂 Mask Batch Repeater
*Category: `Automation/Video`*
The dedicated assembly node for masks. Use this in parallel with the `Image Batch Repeater` to create a synchronized mask timeline.

#### 🔊 Audio Reactive Paster
*Category: `Automation/Video`*
Pastes an overlay image (or an image timeline) onto a background video, with its position animated by the amplitude of an audio signal.
*   **Features**:
    *   Handles both single overlay images and full video timelines as overlays.
    *   Allows for upscaling and downscaling of the overlay image.
    *   Advanced smoothing methods (`Gaussian`, `EMA`, `SMA`) for high-quality motion.
    *   Memory efficient design to handle long videos without crashing.

### Automation/Utils

#### 🔧 Image/Mask Batch Combiner
*Category: `Automation/Utils`*
A crucial utility node that solves a common ComfyUI batching problem. It takes a sequence of individual images/masks (often from an iterated node like `Image Selector by Index`) and merges them into a single, unified batch.
*   **Use Case**: Place this node **directly after** `Image Selector by Index` and before `Image Batch Repeater` to ensure the rest of your workflow runs only once, producing a single video instead of multiple separate ones.

#### 📜 Batch to String
*Category: `Automation/Utils`*
A utility node to convert a list/batch of strings into a single string with a custom separator.

#### 🔢 String to Integer
*Category: `Automation/Utils`*
Converts a string or a batch of strings into integers. It's robust against messy LLM outputs by finding the first number within the text.

#### 📜 String Literal to List Converter
*Category: `Automation/Converters`*
This node takes a string that is a Python list literal (e.g., `"['a', 'b', 'c']"`) and converts it into a proper ComfyUI batch/list output.