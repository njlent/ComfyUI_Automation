# Import all node classes from nodes.py
from .nodes import (
    RssFeedReader, SimpleWebScraper, TargetedWebScraper, LoadImageFromURL,
    StringBatchToString, SRTParser, SRTSceneGenerator, TextOnImage,
    ImageBatchRepeater, LayeredImageProcessor, AudioReactivePaster # Add the new node
)

# A dictionary that maps node CLS names to node display names
NODE_DISPLAY_NAME_MAPPINGS = {
    "RssFeedReader": "📰 RSS Feed Reader",
    "SimpleWebScraper": "🕸️ Simple Web Scraper",
    "TargetedWebScraper": "🎯 Targeted Web Scraper",
    "LoadImageFromURL": "🖼️ Load Image From URL",
    "StringBatchToString": "📜 Batch to String",
    "SRTParser": "🎬 SRT Parser",
    "SRTSceneGenerator": "🎞️ SRT Scene Generator",
    "TextOnImage": "✍️ Text on Image",
    "ImageBatchRepeater": "🔂 Image Batch Repeater",
    "LayeredImageProcessor": "🖼️ Layered Image Processor",
    "AudioReactivePaster": "🔊 Audio Reactive Paster" # Add the display name
}

# A dictionary that maps node CLS names to the node's class
NODE_CLASS_MAPPINGS = {
    # ... (previous mappings) ...
    "LayeredImageProcessor": LayeredImageProcessor,
    "AudioReactivePaster": AudioReactivePaster # Add the class mapping
}

# A friendly message indicating that the nodes have been loaded
print("\033[34mComfyUI_Automation:\033[0m Loaded custom nodes.")

# Export the mappings to ComfyUI
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

print("----------------------------------")
print("### ComfyUI Automation         ###")
print("### Developed by [mimikry.ai]  ###")
print("### Version \033[34mDEV\033[0m                ###")
print("----------------------------------")