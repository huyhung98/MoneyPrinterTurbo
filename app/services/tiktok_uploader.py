"""
TikTok Uploader integration using Playwright.
"""
import os
from loguru import logger
from app.config import config
import threading

class TikTokUploaderService:
    def __init__(self):
        pass

    def is_configured(self) -> bool:
        enabled = config.app.get("tiktok_uploader_enabled", False)
        cookies_file = config.app.get("tiktok_uploader_cookies_file", "")
        return bool(enabled and cookies_file and os.path.exists(cookies_file))

    def upload_video_sync(self, video_path: str, title: str, headless: bool = True):
        try:
            import concurrent.futures
            
            def _worker():
                try:
                    # 👱‍♀️ ponytail: Monkey patch tiktok-uploader to fix broken TikTok DOM changes
                    import tiktok_uploader.upload
                    import time
                    
                    # 1. Skip broken interactivity checkboxes that cause 30s hangs
                    tiktok_uploader.upload._set_interactivity = lambda *args, **kwargs: None
                    
                    # 2. Inject CSS to globally hide joyride tooltips that block typing
                    orig_go_to_upload = tiktok_uploader.upload._go_to_upload
                    def patched_go_to_upload(page):
                        orig_go_to_upload(page)
                        try:
                            page.add_style_tag(content='[class*="joyride"] { display: none !important; pointer-events: none !important; }')
                        except Exception:
                            pass
                    tiktok_uploader.upload._go_to_upload = patched_go_to_upload
        
                    # 3. Fix broken "Post" button selector
                    def patched_post_video(page):
                        time.sleep(3)
                        try:
                            # Chụp ảnh hiện trường trước khi bấm
                            page.screenshot(path="debug_before_post.png", full_page=True)
                            
                            # Click the last button containing 'Post' or 'Đăng'
                            btn = page.locator('button:has-text("Post"), button:has-text("Đăng")').last
                            if btn.is_visible():
                                btn.click()
                                time.sleep(2)
                                
                                # Xử lý cái popup hãm tài "Continue to post?" (Copyright check)
                                try:
                                    post_now_btn = page.locator('button:has-text("Post now"), button:has-text("Đăng ngay")').last
                                    if post_now_btn.is_visible():
                                        post_now_btn.click()
                                except Exception:
                                    pass
                                    
                                # Chờ TikTok xử lý upload
                                time.sleep(10)
                            
                            # Chụp ảnh hiện trường sau khi bấm
                            page.screenshot(path="debug_after_post.png", full_page=True)
                            time.sleep(10)
                        except Exception as e:
                            from loguru import logger
                            logger.warning(f"Post click fallback failed: {e}")
                    tiktok_uploader.upload._post_video = patched_post_video

                    # 4. Fix Mac duplicate description issue (Ctrl+A doesn't work on Mac, must use Meta+A)
                    orig_set_description = tiktok_uploader.upload._set_description
                    def patched_set_description(page, description):
                        try:
                            import platform
                            desc_locator = page.locator(f"xpath={tiktok_uploader.config.selectors.upload.description}")
                            desc_locator.wait_for(state="visible", timeout=5000)
                            desc_locator.click()
                            if platform.system() == "Darwin":
                                desc_locator.press("Meta+A")
                            else:
                                desc_locator.press("Control+A")
                            desc_locator.press("Backspace")
                            time.sleep(0.5)
                        except Exception:
                            pass
                        orig_set_description(page, description)
                    tiktok_uploader.upload._set_description = patched_set_description

                    from tiktok_uploader.upload import upload_video
                    
                    if not os.path.exists(video_path):
                        logger.error(f"TikTok upload failed: Video file not found at {video_path}")
                        return False
                        
                    logger.info(f"Starting Playwright to upload video to TikTok: {video_path}")
                    
                    import json
                    cookies_file = os.path.abspath(config.app.get("tiktok_uploader_cookies_file", ""))
                    
                    kwargs = {}
                    if cookies_file.endswith(".json"):
                        with open(cookies_file, "r") as f:
                            kwargs["cookies_list"] = json.load(f)
                    else:
                        kwargs["cookies"] = cookies_file
                        
                    # Using tiktok_uploader
                    failed_videos = upload_video(
                        filename=video_path,
                        description=title[:2200],
                        headless=headless,
                        **kwargs
                    )
                    
                    if failed_videos and len(failed_videos) > 0:
                        logger.error(f"TikTok upload failed for: {failed_videos}")
                        return False
                        
                    logger.info(f"✅ Video successfully uploaded to TikTok via Playwright!")
                    return True
                except Exception as e:
                    return e

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_worker)
                result = future.result()
                if isinstance(result, Exception):
                    raise result
                return result
            
        except Exception as e:
            logger.error(f"TikTok auto-upload failed: {str(e)}")
            return False

    def upload_video_background(self, video_path: str, title: str):
        if not self.is_configured():
            logger.warning("TikTok Uploader (Playwright) is not configured or cookies file is missing. Skipping auto-upload.")
            return

        logger.info(f"Triggering background upload to TikTok for {video_path}")
        
        # Run in a background thread to prevent blocking the API response
        thread = threading.Thread(
            target=self.upload_video_sync, 
            args=(video_path, title)
        )
        thread.daemon = False
        thread.start()

tiktok_uploader_service = TikTokUploaderService()
