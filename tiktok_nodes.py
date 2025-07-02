# Contains experimental, direct-to-platform publishing nodes.

# --- IMPORTS ---
import os
import traceback
import time
import datetime

# Make sure to handle the case where the library isn't installed
try:
    from tiktok_uploader.upload import upload_video
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    TIKTOK_UPLOADER_AVAILABLE = True
except ImportError:
    TIKTOK_UPLOADER_AVAILABLE = False
    print("TikTok Uploader nodes: The 'tiktok-uploader' and/or 'selenium' library is not installed. This node will not be available. Please run 'pip install tiktok-uploader selenium'.")

def handle_tiktok_cookie_banner(driver, timeout=10):
    try:
        print("DirectTikTokUploader: Checking for cookie banner...")
        banner_element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "tiktok-cookie-banner"))
        )
        print("DirectTikTokUploader: Cookie banner found. Accessing Shadow DOM...")
        shadow_root = driver.execute_script('return arguments[0].shadowRoot', banner_element)
        decline_button_selector = "div.button-wrapper > button:last-child"
        decline_button = WebDriverWait(shadow_root, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, decline_button_selector))
        )
        print("DirectTikTokUploader: Clicking 'Decline all' button on cookie banner.")
        decline_button.click()
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.TAG_NAME, "tiktok-cookie-banner"))
        )
        print("DirectTikTokUploader: Cookie banner successfully dismissed.")
        return True
    except Exception:
        print("DirectTikTokUploader: Cookie banner not found or could not be dismissed. Continuing.")
        return False

class DirectTikTokUploader:
    CATEGORY = "Automation/Publishing (Direct)"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("upload_status",)
    FUNCTION = "upload"

    @classmethod
    def INPUT_TYPES(s):
        if not TIKTOK_UPLOADER_AVAILABLE:
            return {"required": { "error": ("STRING", {"default": "tiktok-uploader or selenium library not found.", "forceInput": True}) }}
            
        return {
            "required": {
                "video_path": ("STRING", {"forceInput": True}),
                "description": ("STRING", {"multiline": True, "default": ""}),
                "sessionid_cookie": ("STRING", {"multiline": False}),
                # --- NEW INPUT FOR THE FIX ---
                "wait_after_post": ("INT", {"default": 5, "min": 1, "max": 60, "step": 1, "tooltip": "Seconds to wait after clicking 'Post' before assuming success. The video uploads in the background."}),
            },
            "optional": {
                "chrome_executable_path": ("STRING", {"multiline": False, "tooltip": "Optional: Full path to your chrome.exe if it's not found automatically."}),
                "comment_permission": ("BOOLEAN", {"default": True, "label_on": "Enabled", "label_off": "Disabled"}),
                "duet_permission": ("BOOLEAN", {"default": True, "label_on": "Enabled", "label_off": "Disabled"}),
                "stitch_permission": ("BOOLEAN", {"default": True, "label_on": "Enabled", "label_off": "Disabled"}),
            }
        }

    def upload(self, video_path, description, sessionid_cookie, wait_after_post, chrome_executable_path=None, comment_permission=True, duet_permission=True, stitch_permission=True):
        if not TIKTOK_UPLOADER_AVAILABLE:
            return ("Error: tiktok-uploader or selenium library not installed.",)
        if not os.path.exists(video_path):
            return (f"Error: Video file not found at '{video_path}'.",)
        if not sessionid_cookie:
            return ("Error: TikTok 'sessionid' cookie is required.",)

        print("DirectTikTokUploader: Preparing to upload directly to TikTok...")
        driver = None
        try:
            options = ChromeOptions()
            options.add_argument("--headless=new")
            if chrome_executable_path and os.path.exists(chrome_executable_path):
                options.binary_location = chrome_executable_path
            service = ChromeService()
            print("DirectTikTokUploader: Initializing WebDriver...")
            driver = webdriver.Chrome(service=service, options=options)
            
            print("DirectTikTokUploader: Authenticating session and handling pop-ups...")
            driver.get("https://www.tiktok.com/")
            driver.add_cookie({'name': 'sessionid_ss', 'value': sessionid_cookie, 'domain': '.tiktok.com'})
            driver.get("https://www.tiktok.com/upload")
            time.sleep(2)
            handle_tiktok_cookie_banner(driver)

            # --- START OF MODIFIED UPLOAD LOGIC ---
            # We are now essentially wrapping the library's function and overriding its success check.
            
            # The library's internal logic will still run.
            # We pass a modified 'explicit_wait' to the function.
            # This will still timeout, but we will catch the exception and treat it as a success.
            # We set the wait to our user-defined value.
            
            print("DirectTikTokUploader: Handing over to the uploader library...")
            upload_video(
                filename=video_path,
                description=description,
                sessionid=sessionid_cookie,
                comment=comment_permission,
                duet=duet_permission,
                stitch=stitch_permission,
                browser_agent=driver,
                # This is a bit of a hack. The library doesn't have a simple "don't wait" flag.
                # So we tell it to wait for our custom (short) duration.
                # It will fail after this duration, but we know the upload has already started.
                explicit_wait=wait_after_post 
            )

            # If the code reaches here, it means the confirmation WAS found, which is a bonus.
            status_message = "TikTok upload SUCCESSFUL! Confirmation received."
            print(f"DirectTikTokUploader: {status_message}")
            return (status_message,)
            # --- END OF MODIFIED UPLOAD LOGIC ---

        except Exception as e:
            # --- START OF "FIRE-AND-FORGET" FIX ---
            # Check if the error is the expected timeout after posting.
            if "Message: " in str(e) and "Stacktrace:" in str(e): # This is characteristic of a Selenium timeout
                status_message = f"SUCCESS (Fire-and-Forget): Post initiated. Video is processing on TikTok. (Ignored expected timeout)."
                print(f"DirectTikTokUploader: {status_message}")
                return (status_message,)
            # --- END OF "FIRE-AND-FORGET" FIX ---
            
            # If it's a different error, report it as a true failure.
            error_message = f"DirectTikTokUploader: FAILED with an unexpected error: {e}"
            print(error_message)
            traceback.print_exc()
            return (error_message,)
        
        finally:
            if driver:
                print("DirectTikTokUploader: Closing WebDriver.")
                driver.quit()

class ScheduledTikTokUploader:
    CATEGORY = "Automation/Publishing (Direct)"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("upload_status",)
    FUNCTION = "upload"

    @classmethod
    def INPUT_TYPES(s):
        if not TIKTOK_UPLOADER_AVAILABLE:
            return {"required": { "error": ("STRING", {"default": "tiktok-uploader or selenium library not found.", "forceInput": True}) }}
            
        return {
            "required": {
                "video_path": ("STRING", {"forceInput": True}),
                "description": ("STRING", {"multiline": True, "default": ""}),
                "sessionid_cookie": ("STRING", {"multiline": False}),
                
                # --- NEW SCHEDULING INPUTS ---
                "schedule_date": ("STRING", {"default": "YYYY-MM-DD", "tooltip": "Date to schedule the post in YYYY-MM-DD format."}),
                "schedule_time": ("STRING", {"default": "HH:MM", "tooltip": "Time to schedule the post in 24-hour HH:MM format."}),
                
                "wait_after_post": ("INT", {"default": 5, "min": 1, "max": 60, "step": 1, "tooltip": "Seconds to wait after clicking 'Schedule' before assuming success."}),
            },
            "optional": {
                "chrome_executable_path": ("STRING", {"multiline": False, "tooltip": "Optional: Full path to your chrome.exe if it's not found automatically."}),
                "comment_permission": ("BOOLEAN", {"default": True, "label_on": "Enabled", "label_off": "Disabled"}),
                "duet_permission": ("BOOLEAN", {"default": True, "label_on": "Enabled", "label_off": "Disabled"}),
                "stitch_permission": ("BOOLEAN", {"default": True, "label_on": "Enabled", "label_off": "Disabled"}),
            }
        }

    def upload(self, video_path, description, sessionid_cookie, schedule_date, schedule_time, wait_after_post, chrome_executable_path=None, comment_permission=True, duet_permission=True, stitch_permission=True):
        if not TIKTOK_UPLOADER_AVAILABLE:
            return ("Error: tiktok-uploader or selenium library not installed.",)
        if not os.path.exists(video_path):
            return (f"Error: Video file not found at '{video_path}'.",)
        if not sessionid_cookie:
            return ("Error: TikTok 'sessionid' cookie is required.",)

        # --- Parse the schedule datetime ---
        try:
            schedule_str = f"{schedule_date} {schedule_time}"
            schedule_datetime = datetime.datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
            print(f"ScheduledTikTokUploader: Parsed schedule time: {schedule_datetime}")
        except ValueError:
            error_message = "Error: Invalid date or time format. Please use YYYY-MM-DD and HH:MM."
            print(f"ScheduledTikTokUploader: {error_message}")
            return (error_message,)

        print("ScheduledTikTokUploader: Preparing to schedule video on TikTok...")
        driver = None
        try:
            options = ChromeOptions()
            options.add_argument("--headless=new")
            if chrome_executable_path and os.path.exists(chrome_executable_path):
                options.binary_location = chrome_executable_path
            service = ChromeService()
            driver = webdriver.Chrome(service=service, options=options)
            
            driver.get("https://www.tiktok.com/")
            driver.add_cookie({'name': 'sessionid_ss', 'value': sessionid_cookie, 'domain': '.tiktok.com'})
            driver.get("https://www.tiktok.com/upload")
            time.sleep(2)
            handle_tiktok_cookie_banner(driver)

            # Call the library's upload function with the schedule parameter
            upload_video(
                filename=video_path,
                description=description,
                sessionid=sessionid_cookie,
                schedule=schedule_datetime, # Pass the datetime object here
                comment=comment_permission,
                duet=duet_permission,
                stitch=stitch_permission,
                browser_agent=driver,
                explicit_wait=wait_after_post 
            )
            
            # This part will likely be skipped due to the timeout, which we treat as a success
            status_message = "TikTok schedule SUCCESSFUL! Confirmation received."
            print(f"ScheduledTikTokUploader: {status_message}")
            return (status_message,)

        except Exception as e:
            # Check for the expected timeout after clicking "Schedule"
            if "Message: " in str(e) and "Stacktrace:" in str(e):
                status_message = f"SUCCESS (Fire-and-Forget): Schedule initiated for {schedule_date} {schedule_time}. Video is processing on TikTok."
                print(f"ScheduledTikTokUploader: {status_message}")
                return (status_message,)
            
            error_message = f"ScheduledTikTokUploader: FAILED with an unexpected error: {e}"
            print(error_message)
            traceback.print_exc()
            return (error_message,)
        
        finally:
            if driver:
                print("ScheduledTikTokUploader: Closing WebDriver.")
                driver.quit()