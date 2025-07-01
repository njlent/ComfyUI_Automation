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
*   [**Mask Batch Repeater**](#-mask-batch-repeater)
*   [**Audio Reactive Paster**](#-audio-reactive-paster)
*   [**Image Selector by Index**](#️-image-selector-by-index)
*   [**String to Integer**](#-string-to-integer)
*   [**List Flattener**](#-list-flattener)

---

## Installation

1.  Navigate to your `ComfyUI/custom_nodes/` directory.
2.  Clone this repository into that directory:
    ```bash
    git clone <your-repository-url-here> ComfyUI_Automation
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
Creates a layered image effect by placing a padded version of an image on top of a blurred, full-screen version of the same image. Fully batch-aware.

#### ✍️ Text on Image
*Category: `Automation/Image`*
Draws text onto an image with various formatting options. Intelligently handles batches of images and/or text.

#### 🖼️🎭 Image Selector by Index
*Category: `Automation/Image`*
Selects and loads a batch of images from a directory based on a corresponding batch of indices (numbers). This is the key node for creating emotion-driven character animations.

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
Parses SRT (subtitle) formatted text to extract timing and content. **This node is batch-compatible**; if you feed it a list of SRT strings, its outputs will be nested lists.

*   **Inputs**:
    *   `srt_content`: The full text of an `.srt` file, or a batch of SRT strings.
    *   `handle_pauses`: `Include Pauses` creates blank entries for silent gaps to maintain perfect timing.
*   **Outputs**:
    *   `text_batch`, `start_ms_batch`, `end_ms_batch`, `duration_ms_batch`: The core data from the script.
    *   `section_count`: A total count of all outputted sections (subtitles + pauses).

#### 🎞️ SRT Scene Generator
*Category: `Automation/Video`*
Generates a timeline of blank frames based on timing data. **This node expects a flat list of durations.** If using a batched `SRT Parser`, you must use a `List Flattener` node first.

*   **Inputs**:
    *   `duration_ms_batch`: A **flat** list of durations in milliseconds.
    *   `fps`, `width`, `height`: Standard video settings.
*   **Outputs**:
    *   `image_timeline`: A single, long batch of blank frames representing the entire video duration.
    *   `start_frame_indices`, `frame_counts`: Critical timing data for assembling your video content.

#### 🔂 Image Batch Repeater
*Category: `Automation/Video`*
The core assembly node for images. It takes a batch of content images and repeats each one according to a list of frame counts.

*   **Inputs**:
    *   `image`: A batch of content images (e.g., character faces).
    *   `repeat_counts`: The list of frame durations. Connect `frame_counts` from `SRT Scene Generator` here.
*   **Outputs**:
    *   `image_timeline`: A finished video timeline with your images correctly placed and timed.

#### 🔂 Mask Batch Repeater
*Category: `Automation/Video`*
The dedicated assembly node for masks. It takes a batch of masks and repeats each one according to a list of frame counts. Use this in parallel with the `Image Batch Repeater`.

*   **Inputs**:
    *   `mask`: A batch of masks (e.g., for character faces).
    *   `repeat_counts`: The list of frame durations. Connect `frame_counts` from `SRT Scene Generator` here.
*   **Outputs**:
    *   `mask_timeline`: A finished mask timeline, perfectly synchronized with the image timeline.

#### 🔊 Audio Reactive Paster
*Category: `Automation/Video`*
Pastes an overlay image onto a background video, with its position animated by the amplitude of an audio signal.

*   **Inputs**:
    *   `background_image`, `overlay_image`, `overlay_mask`, `audio`, `fps`: Core inputs.
    *   `x_strength` / `y_strength`: Controls motion amount. **Use negative values to invert the direction.**
    *   `smoothing_method`: Choose between `Gaussian`, `EMA`, or `SMA` for different motion styles.
*   **Outputs**:
    *   `image_timeline`: The final composited video.
    *   `amplitude_visualization`: A graph of the audio amplitude over time, for debugging and visual feedback.

### Automation/Utils

#### 📜 Batch to String
*Category: `Automation/Utils`*
A utility node to convert a list/batch of strings into a single string.

#### 🔢 String to Integer
*Category: `Automation/Utils`*
Converts a string or a batch of strings into integers. It's robust against messy LLM outputs by finding the first number within the text.

*   **Use Case**: Place this node after an LLM node to convert its textual number output (e.g., "The emotion is: 3") into a clean integer (`3`) for the `Image Selector by Index` node.

#### 🐍 List Flattener
*Category: `Automation/Utils`*
A crucial utility that takes a nested list (e.g., `[[a, b], [c]]`) and "flattens" it into a single, simple list (e.g., `[a, b, c]`).

*   **Use Case**: Place this node after a batched `SRT Parser` and before the `SRT Scene Generator` to ensure the generator receives the clean, flat list of durations it expects.