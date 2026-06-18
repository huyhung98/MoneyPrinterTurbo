import logging
from loguru import logger
from tiktok_uploader import config as tk_config
tk_config.implicit_wait = 1  # reduce wait time

from app.services.tiktok_uploader import tiktok_uploader_service

def test():
    # pass headless=False
    success = tiktok_uploader_service.upload_video_sync("sample_video.mp4", "Local Test Video #test #moneyprinterturbo", headless=False)
    print("Success?", success)

if __name__ == "__main__":
    test()
