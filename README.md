# ComfyUI Automation Node Pack

This is a collection of nodes for automating workflows in ComfyUI.

## Installation

1.  Navigate to your `ComfyUI/custom_nodes/` directory.
2.  Clone this repository:
    ```bash
    git clone <your-repo-url-here> ComfyUI_Automation
    ```
    (Or just copy the `ComfyUI_Automation` folder here).
3.  Restart ComfyUI. It should automatically detect the `requirements.txt` and install the necessary `feedparser` library. If not, you can install it manually:
    ```bash
    pip install -r ComfyUI/custom_nodes/ComfyUI_Automation/requirements.txt
    ```
4.  Restart ComfyUI one more time.

## Nodes

### 📰 RSS Feed Reader

This node fetches data from one or more RSS feeds and provides the content as strings or synchronized batches.

#### Inputs

-   **`links`**: A multiline text box for one or more RSS feed URLs, each on a new line.
-   **`max_entries`**: An integer to limit how many of the latest entries to fetch from *each* feed.
-   **`batch_source`**: A dropdown to select what content to use for the `content_batch` output. Options are `title`, `summary`, or `link`.
-   **`output_mode`**: A dropdown to control the format of the outputs.
    -   `Concatenated String`: The first two outputs are single, large strings.
    -   `Batch Output`: All three outputs are batches (lists), synchronized by entry.

#### Outputs

-   **`raw_text_output`**:
    -   If `output_mode` is `Concatenated String`: A single string containing a simple concatenation of the titles and summaries of all fetched entries.
    -   If `output_mode` is `Batch Output`: A batch where each item is the raw text for a single RSS entry.
-   **`formatted_text_output`**:
    -   If `output_mode` is `Concatenated String`: A single, more readable string with labels for Title, Link, and Summary for all entries.
    -   If `output_mode` is `Batch Output`: A batch where each item is the fully formatted text block for a single RSS entry.
-   **`content_batch`**: (This is always a batch). It contains the content specified by the `batch_source` input. It can be connected to any input that accepts a batch of strings (like a prompt input).