import traceback

# A dictionary of all nodes to be loaded, mapping class name to display name
# This is the "master list" of all nodes in the pack.
NODES_TO_LOAD = {
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
    "AudioReactivePaster": "🔊 Audio Reactive Paster"
}

# These will be populated automatically
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

print("----------------------------------")
print("### ComfyUI Automation         ###")
print("### Developed by [mimikry.ai]  ###")
print("### Version \033[34mDEV\033[0m                ###")
print("###")

# --- Dynamically load nodes ---
for class_name, display_name in NODES_TO_LOAD.items():
    try:
        # Dynamically import the class from nodes.py
        node_class = getattr(__import__('custom_nodes.ComfyUI_Automation.nodes', fromlist=[class_name]), class_name)
        
        # Add the class and its display name to the mappings
        NODE_CLASS_MAPPINGS[class_name] = node_class
        NODE_DISPLAY_NAME_MAPPINGS[class_name] = display_name
        
        print(f"###   \033[92m+ Loaded Node:\033[0m {class_name} -> {display_name}")

    except AttributeError:
        # This happens if the class is not found in the file
        print(f"###   \033[91m- FAILED to load Node:\033[0m '{class_name}'. Class not found in nodes.py. This is likely due to a syntax error preventing the file from being read correctly.")
    except Exception as e:
        # This will catch any other errors, like syntax errors
        print(f"###   \03g[91m- FAILED to load Node:\033[0m '{class_name}'. An error occurred during import.")
        # Print the full traceback to help debug
        traceback.print_exc()

print(f"### \033[34mComfyUI_Automation:\033[0m Successfully loaded {len(NODE_CLASS_MAPPINGS)} out of {len(NODES_TO_LOAD)} nodes.")
# Export the mappings to ComfyUI
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

print("----------------------------------")