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
    git clone https://github.com/njlent/ComfyUI_Automation ComfyUI_Automation
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

### Automation/Video

#### 🎬 SRT Parser
*Category: `Automation/Video`*
Parses SRT (subtitle) formatted text to extract timing and content. Batch-compatible with a properly formatted `text_list` output.

#### 🎞️ SRT Scene Generator
*Category: `Automation/Video`*
Generates a timeline of blank frames based on a flat list of durations from the `SRT Parser`.

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
*Category. `Automation/Utils`*
Converts a string or a batch of strings into integers. It's robust against messy LLM outputs by finding the first number within the text.

#### 📜 String Literal to List Converter
*Category: `Automation/Converters`*
This node takes a string that is a Python list literal (e.g., `"['a', 'b', 'c']"`) and converts it into a proper ComfyUI batch/list output.