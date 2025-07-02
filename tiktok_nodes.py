# File: njlent-comfyui_automation/tiktok_nodes.py
# Contains experimental, direct-to-platform publishing nodes.

# --- IMPORTS ---
import os
import traceback
from tiktok_uploader.upload import upload_video
from tiktok_uploader.auth import AuthBackend

# Make sure to handle the case where the library isn't installed
try:
    from tiktok_uploader.upload import upload_video
    from tiktok_uploader.auth import AuthBackend
    TIKTOK_UPLOADER_AVAILABLE = True
except ImportError:
    TIKTOK_UPLOADER_AVAILABLE = False
    print("TikTok Uploader nodes: The 'tiktok-uploader' library is not installed. This node will not be available. Please run 'pip install tiktok-uploader undetected-chromedriver'.")


class DirectTikTokUploader:
    CATEGORY = "Automation/Publishing (Direct)"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("upload_status",)
    FUNCTION = "upload"

    @classmethod
    def INPUT_TYPES(s):
        # If the library isn't installed, we can't show the node.
        # A better way is to conditionally register it, but for simplicity here,
        # we'll let it error out if someone tries to use it without the library.
        if not TIKTOK_UPLOADER_AVAILABLE:
            return {"required": {
                "error": ("STRING", {"default": "tiktok-uploader library not found. Please install it.", "forceInput": True})
            }}
            
        privacy_options = ["PUBLIC", "PRIVATE", "FRIENDS"]

        return {
            "required": {
                "video_path": ("STRING", {"forceInput": True, "tooltip": "The file path of the video to upload."}),
                "description": ("STRING", {"multiline": True, "default": "", "tooltip": "The description/caption for the video. Supports #hashtags and @mentions."}),
                "sessionid_cookie": ("STRING", {"multiline": False, "tooltip": "Your 'sessionid_ss' cookie from a logged-in TikTok session in your browser."}),
                "privacy_type": (privacy_options, {"default": "PUBLIC", "tooltip": "Set the privacy level of the uploaded video."}),
            },
            "optional": {
                "thumbnail_path": ("STRING", {"forceInput": True, "tooltip": "Optional: Path to a custom thumbnail. If not provided, TikTok will select one."}),
                "comment_permission": ("BOOLEAN", {"default": True, "label_on": "Enabled", "label_off": "Disabled"}),
                "duet_permission": ("BOOLEAN", {"default": True, "label_on": "Enabled", "label_off": "Disabled"}),
                "stitch_permission": ("BOOLEAN", {"default": True, "label_on": "Enabled", "label_off": "Disabled"}),
            }
        }

    def upload(self, video_path, description, sessionid_cookie, privacy_type, thumbnail_path=None, comment_permission=True, duet_permission=True, stitch_permission=True):
        if not TIKTOK_UPLOADER_AVAILABLE:
            return ("Error: tiktok-uploader library not installed.",)
            
        if not os.path.exists(video_path):
            return (f"Error: Video file not found at '{video_path}'.",)
            
        if not sessionid_cookie:
            return ("Error: TikTok 'sessionid_ss' cookie is required for authentication.",)

        print("DirectTikTokUploader: Preparing to upload directly to TikTok...")

        try:
            # --- Authentication ---
            # The library manages the browser automation in the background
            auth = AuthBackend(cookies_path=None, cookies=[{'name': 'sessionid_ss', 'value': sessionid_cookie}])
            
            # --- Thumbnail Logic ---
            # The library takes a timestamp in seconds for the thumbnail.
            # If a path is provided, we can't use it directly. We tell the user to use TikTok's selector.
            # A more advanced implementation could use ffmpeg to extract the frame number, but that's a new dependency.
            # For now, we'll let TikTok auto-select or the user can edit it later.
            # The library's `thumbnail` parameter expects a timestamp, not a path. So we ignore `thumbnail_path`.
            if thumbnail_path:
                print("DirectTikTokUploader: Warning - Custom thumbnail path is not directly supported by this uploader method. Please select a thumbnail on TikTok after uploading.")

            # --- Map Permissions ---
            # 0: Everyone, 1: Friends, 2: Private (for comments)
            # 0: Everyone, 1: Friends (for duet/stitch)
            comment_perm = 0 if comment_permission else 2
            duet_perm = 0 if duet_permission else 1
            stitch_perm = 0 if stitch_permission else 1
            
            # --- Upload ---
            # The `upload_video` function is blocking and can take a long time.
            # It returns the URL of the uploaded video on success.
            failed, url = upload_video(
                filename=video_path,
                description=description,
                auth=auth,
                # The library doesn't seem to have a direct privacy setting in the upload call itself.
                # This is a limitation of the unofficial API. It often defaults to the user's last setting.
                # The workaround is to set it manually after upload or use the web UI.
                # The `privacy_type` argument is for our UI but we can't pass it directly here.
                # We'll add a note about this.
                comment=comment_perm,
                duet=duet_perm,
                stitch=stitch_perm,
                # proxy=None, # Optional proxy
            )
            
            if failed:
                status_message = f"TikTok upload FAILED. URL: {url}"
            else:
                status_message = f"TikTok upload SUCCESSFUL! Video is available at: {url}"

            print(f"DirectTikTokUploader: {status_message}")
            if privacy_type != "PUBLIC":
                 print(f"DirectTikTokUploader: NOTE - Please verify the video's privacy is set to '{privacy_type}' on TikTok, as the API may not set this reliably.")

            return (status_message,)

        except Exception as e:
            error_message = f"DirectTikTokUploader: FAILED. Error: {e}"
            print(error_message)
            traceback.print_exc()
            return (error_message,)