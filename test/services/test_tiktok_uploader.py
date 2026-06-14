import os
import pytest
from unittest.mock import patch, MagicMock

from app.config import config
from app.services.tiktok_uploader import tiktok_uploader_service

def test_is_configured_true(tmp_path):
    # Mock config
    config.app["tiktok_uploader_enabled"] = True
    
    # Create a fake cookies file
    cookies_file = tmp_path / "cookies.txt"
    cookies_file.write_text("fake cookies")
    config.app["tiktok_uploader_cookies_file"] = str(cookies_file)
    
    assert tiktok_uploader_service.is_configured() is True

def test_is_configured_false_missing_file():
    config.app["tiktok_uploader_enabled"] = True
    config.app["tiktok_uploader_cookies_file"] = "non_existent_file.txt"
    
    assert tiktok_uploader_service.is_configured() is False

def test_is_configured_false_disabled(tmp_path):
    config.app["tiktok_uploader_enabled"] = False
    
    cookies_file = tmp_path / "cookies.txt"
    cookies_file.write_text("fake cookies")
    config.app["tiktok_uploader_cookies_file"] = str(cookies_file)
    
    assert tiktok_uploader_service.is_configured() is False

@patch("tiktok_uploader.upload.upload_video")
def test_upload_video_sync_success(mock_upload_video, tmp_path):
    # Setup fake video file
    video_file = tmp_path / "video.mp4"
    video_file.write_text("fake video content")
    
    # Mock config
    config.app["tiktok_uploader_cookies_file"] = "cookies.txt"
    
    result = tiktok_uploader_service.upload_video_sync(str(video_file), "Test Title")
    
    assert result is True
    mock_upload_video.assert_called_once_with(
        filename=str(video_file),
        description="Test Title",
        cookies="cookies.txt"
    )

@patch("tiktok_uploader.upload.upload_video")
def test_upload_video_sync_missing_video(mock_upload_video):
    result = tiktok_uploader_service.upload_video_sync("non_existent_video.mp4", "Test Title")
    
    assert result is False
    mock_upload_video.assert_not_called()

@patch("app.services.tiktok_uploader.threading.Thread")
@patch("app.services.tiktok_uploader.TikTokUploaderService.is_configured")
def test_upload_video_background(mock_is_configured, mock_thread):
    mock_is_configured.return_value = True
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance
    
    tiktok_uploader_service.upload_video_background("video.mp4", "Title")
    
    mock_thread.assert_called_once()
    mock_thread_instance.start.assert_called_once()
    assert mock_thread_instance.daemon is True
