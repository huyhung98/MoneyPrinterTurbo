import tiktok_uploader.upload
tiktok_uploader.upload._set_interactivity = lambda *args, **kwargs: None

from app.services.tiktok_uploader import tiktok_uploader_service

success = tiktok_uploader_service.upload_video_sync("sample_video.mp4", "Local Test Video #test #moneyprinterturbo", headless=True)
print("Success:", success)
