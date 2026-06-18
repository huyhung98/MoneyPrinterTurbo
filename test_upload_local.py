import os
import sys

import logging
from tiktok_uploader import logger, config
logger.setLevel(logging.DEBUG)
config.quit_on_end = False

from app.services.tiktok_uploader import tiktok_uploader_service

def test_upload():
    # 1. Check configuration
    if not tiktok_uploader_service.is_configured():
        print("❌ TikTok uploader is NOT configured correctly.")
        print("Ensure 'tiktok_uploader_cookies_file' in config.toml points to a valid file.")
        return

    # 2. Prepare a dummy video file if it doesn't exist
    sample_video_path = "sample_video.mp4"
    if not os.path.exists(sample_video_path):
        print(f"⚠️ Dummy video '{sample_video_path}' not found, creating a tiny dummy file...")
        # A tiny valid empty mp4 might not be accepted by TikTok, 
        # so it's better if you replace this with a real short video if TikTok rejects it!
        with open(sample_video_path, "wb") as f:
            f.write(b"\x00" * 1024 * 100)  # Just a dummy 100KB file

    sample_title = "Local Test Video #test #moneyprinterturbo"

    print("🚀 Starting TikTok video upload test (HEADLESS = FALSE)...")
    print("👀 You should see a browser window pop up shortly!")
    
    # We pass headless=False so you can visually watch what Playwright is doing
    success = tiktok_uploader_service.upload_video_sync(
        video_path=sample_video_path, 
        title=sample_title,
        headless=False  
    )
    
    if success:
        print("✅ Upload test completed successfully!")
    else:
        print("❌ Upload test failed. See browser window or logs for details.")
        
    print("⏳ Waiting 10 minutes so you can inspect the browser...")
    import time
    time.sleep(600)

if __name__ == "__main__":
    test_upload()
