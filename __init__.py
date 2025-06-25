"""
@author: Your Name
@title: ComfyUI Automation
@nickname: Automation
@description: A collection of nodes for automating workflows in ComfyUI, starting with an RSS feed reader.
"""

# Import the node class from the nodes.py file
from .nodes import RssFeedReader, SimpleWebScraper, TargetedWebScraper, LoadImageFromURL

# A dictionary that maps node CLS names to node display names
NODE_DISPLAY_NAME_MAPPINGS = {
    "RssFeedReader": "📰 RSS Feed Reader",
    "SimpleWebScraper": "🕸️ Simple Web Scraper",
    "TargetedWebScraper": "🎯 Targeted Web Scraper",
    "LoadImageFromURL": "🖼️ Load Image From URL"
}

# A dictionary that maps node CLS names to the node's class
NODE_CLASS_MAPPINGS = {
    "RssFeedReader": RssFeedReader,
    "SimpleWebScraper": SimpleWebScraper,
    "TargetedWebScraper": TargetedWebScraper,
    "LoadImageFromURL": LoadImageFromURL
}

# A friendly message indicating that the nodes have been loaded
print("\033[34mComfyUI_Automation:\033[0m Loaded custom nodes.")

# Export the mappings to ComfyUI
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

print("\033[34m----------------------------------")
print("### ComfyUI Automation         ###")
print("### Developed by [mimikry.ai   ###")
print("### Version DEV                ###")
print("----------------------------------\033[0m")