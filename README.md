# File: ComfyUI_Automation/README.md

# ComfyUI Automation Node Pack

This is a collection of nodes for automating workflows in ComfyUI.

## Installation

1.  Navigate to your `ComfyUI/custom_nodes/` directory.
2.  Clone this repository:
    ```bash
    git clone <your-repo-url-here> ComfyUI_Automation
    ```
    (Or just copy the `ComfyUI_Automation` folder here).
3.  Restart ComfyUI. It will automatically detect the `requirements.txt` and ask you to install the dependencies. If it doesn't, you can install them manually:
    ```bash
    cd ComfyUI_Automation
    pip install -r requirements.txt
    ```
4.  Restart ComfyUI one more time.

## Nodes

### 📰 RSS Feed Reader

This node fetches data from one or more RSS feeds.

#### Inputs

-   **`links`**: A multiline text box where you can paste one or more RSS feed URLs, each on a new line.
-   **`max_entries`**: An integer to limit how many of the latest entries to fetch from *each* feed.
-   **`batch_source`**: A dropdown to select what content to use for the `content_batch` output. Options are `title`, `summary`, or `link`.

#### Outputs

-   **`raw_text`**: A single string containing a simple concatenation of the titles and summaries of all fetched entries.
-   **`formatted_text`**: A single, more readable string with labels for Title, Link, and Summary for each entry.
-   **`content_batch`**: **This is a batch output (a list of strings).** It can be connected to any input that accepts a batch of strings (like the prompt input on many samplers). The content of this batch is determined by the `batch_source` input.