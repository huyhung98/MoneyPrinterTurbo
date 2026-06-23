import os
import time
import shutil
from pathlib import Path

# Add project root to path so we can import app modules
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.tiktok_uploader import tiktok_uploader_service

import glob

# Tự động tìm đường dẫn Google Drive chuẩn trên macOS (phiên bản mới)
gdrive_paths = glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*"))
if gdrive_paths:
    root_gdrive = gdrive_paths[0]
    # File Provider của Mac thường dùng tên "My Drive" (có dấu cách)
    if os.path.exists(os.path.join(root_gdrive, "My Drive")):
        BASE_DIR = os.path.join(root_gdrive, "My Drive/TiktokUploads")
    else:
        BASE_DIR = os.path.join(root_gdrive, "MyDrive/TiktokUploads")
else:
    BASE_DIR = os.path.expanduser("~/Google Drive/MyDrive/TiktokUploads")

try:
    os.makedirs(BASE_DIR, exist_ok=True)
except PermissionError:
    print(f"❌ LỖI RỒI SẾP: Không có quyền truy cập vào Google Drive ({BASE_DIR}).")
    print("Sếp gõ thử lệnh này vào Terminal để nó hiện popup xin quyền nhé:")
    print("cd ~/Library/CloudStorage/GoogleDrive-huyo.hung99@gmail.com")
    import sys
    sys.exit(1)

WATCH_DIR = os.path.join(BASE_DIR, "Pending")
DONE_DIR = os.path.join(BASE_DIR, "Done")
FAILED_DIR = os.path.join(BASE_DIR, "Failed")

def is_file_ready(filepath):
    """Kiểm tra xem file đã tải xong từ Google Drive chưa bằng cách so sánh dung lượng"""
    try:
        size1 = os.path.getsize(filepath)
        time.sleep(2)
        size2 = os.path.getsize(filepath)
        return size1 == size2 and size1 > 0
    except OSError:
        return False

def main():
    # Tạo sẵn các thư mục nếu chưa có
    for d in [WATCH_DIR, DONE_DIR, FAILED_DIR]:
        os.makedirs(d, exist_ok=True)
        
    print(f"👱‍♀️ Ponytail Watcher: Đang lườm thư mục: {WATCH_DIR}")
    print("Cứ thả video vào đây, mình sẽ ném lên TikTok giúp bạn...\n")
    
    while True:
        try:
            for filename in os.listdir(WATCH_DIR):
                if not filename.lower().endswith(".mp4"):
                    continue
                    
                filepath = os.path.join(WATCH_DIR, filename)
                
                # Bỏ qua nếu file đang trong quá trình đồng bộ (size thay đổi)
                if not is_file_ready(filepath):
                    continue
                    
                print(f"🚀 Phóng lợn... à nhầm, phát hiện video mới: {filename}")
                
                # Tên file sẽ được dùng làm Tiêu đề (bạn có thể chèn hashtag trực tiếp vào tên file)
                title = Path(filename).stem
                
                # Upload!
                success = tiktok_uploader_service.upload_video_sync(filepath, title)
                
                if success:
                    print(f"✅ Lên thớt thành công: {filename}. Chuyển sang thư mục Done.\n")
                    shutil.move(filepath, os.path.join(DONE_DIR, filename))
                else:
                    print(f"❌ Xịt rồi: {filename}. Chuyển sang thư mục Failed để tránh lặp.\n")
                    shutil.move(filepath, os.path.join(FAILED_DIR, filename))
                    
        except Exception as e:
            print(f"Lỗi rồi sếp: {e}")
            
        # Lười biếng nghỉ 5 giây rồi mới quét tiếp
        time.sleep(5)

if __name__ == "__main__":
    main()
