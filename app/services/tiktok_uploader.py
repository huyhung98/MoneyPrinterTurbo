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

    def upload_video_sync(self, video_path: str, title: str):
        try:
            from tiktok_uploader.upload import upload_video
            
            if not os.path.exists(video_path):
                logger.error(f"TikTok upload failed: Video file not found at {video_path}")
                return False
                
            logger.info(f"Starting Playwright to upload video to TikTok: {video_path}")
            
            cookies_file = config.app.get("tiktok_uploader_cookies_file", "")
            # Using tiktok_uploader
            upload_video(
                filename=video_path,
                description=title[:2200],
                cookies=cookies_file
            )
            
            logger.info(f"✅ Video successfully uploaded to TikTok via Playwright!")
            return True
            
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
        thread.daemon = True
        thread.start()

tiktok_uploader_service = TikTokUploaderService()
