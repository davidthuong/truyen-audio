import os
import shutil
import json
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RELEASE_DIR = BASE_DIR / "Ban_Clean_Chia_Se" / "AudioStoryStudio_Clean"
DIST_APP_DIR = BASE_DIR / "dist" / "AudioStoryStudio"

def create_clean_package():
    print("=" * 60)
    print("   DANG TAO BAN MOI (CLEAN) - KHONG DUNG DANG CA NHAN")
    print("=" * 60)

    # 1. Tao thu muc Release hoan toan doc lap
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Sao chep bo chuong trinh .exe va _internal sang thu muc rieng
    print("[*] Dang sao chep AudioStoryStudio.exe va thu vien sang thu muc rieng...")
    shutil.copy2(DIST_APP_DIR / "AudioStoryStudio.exe", RELEASE_DIR / "AudioStoryStudio.exe")
    
    target_internal = RELEASE_DIR / "_internal"
    if target_internal.exists():
        shutil.rmtree(target_internal)
    shutil.copytree(DIST_APP_DIR / "_internal", target_internal)

    # 3. Tao file settings.json trang tinh (Khong luu API Key hay Token ca nhan)
    clean_settings = {
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "chat_model": "gpt-4o-mini",
        "image_model": "dall-e-3",
        "image_provider": "pollinations",
        "default_voice": "vi-VN-HoaiMyNeural",
        "default_bgm_volume": 0.15
    }
    with open(RELEASE_DIR / "settings.json", "w", encoding="utf-8") as f:
        json.dump(clean_settings, f, indent=4, ensure_ascii=False)

    # 4. Tao file scheduler_config.json mac dinh sach se
    clean_scheduler = {
        "enabled": False,
        "scheduled_times": ["08:00", "12:30", "19:30"],
        "mode": "ai_auto",
        "topic_queue": [
            "[Tổng Tài] 3 năm sau, tôi trở về thâu tóm công ty của kẻ phản bội",
            "[Kinh Dị] Bí mật ngôi làng cổ bị bỏ hoang trong rừng sâu lúc nửa đêm",
            "[Tiên Hiệp] Đệ tử ngoại môn trùng sinh nghịch thiên cải mệnh",
            "[Lofi] Chuyện tình dang dở dưới cơn mưa mùa thu Hà Nội"
        ],
        "genre": "random_all",
        "duration": 5,
        "voice": "vi-VN-HoaiMyNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "bgm_name": "",
        "bgm_volume": 0.15,
        "aspect_ratio": "16:9",
        "enable_waveform": True,
        "auto_upload_youtube": False,
        "privacy_status": "unlisted",
        "last_run_date": "",
        "executed_slots_today": []
    }
    with open(RELEASE_DIR / "scheduler_config.json", "w", encoding="utf-8") as f:
        json.dump(clean_scheduler, f, indent=2, ensure_ascii=False)

    # 5. Tao thu muc output va temp rong
    (RELEASE_DIR / "output").mkdir(exist_ok=True)
    (RELEASE_DIR / "temp").mkdir(exist_ok=True)

    # 6. Tao file Huong_Dan_Su_Dung.txt
    huong_dan = """============================================================
       AUDIOSTORY STUDIO - PHẦN MỀM TẠO VIDEO TRUYỆN AUDIO AI
============================================================

1. CÁCH KHỞI ĐỘNG:
- Nhấp đúp vào file: AudioStoryStudio.exe để mở ứng dụng.

2. CÀI ĐẶT API (Nếu có):
- Bấm nút "Cài Đặt API" trên góc phải ứng dụng để nhập OpenAI API Key / Proxy API.
- Nếu không có API Key, hệ thống vẫn tự động tạo truyện và vẽ ảnh AI miễn phí!

3. KẾT NỐI KÊNH YOUTUBE & LÊN LỊCH AUTO-PILOT:
- Chuyển sang Tab "2. Lên Lịch & Auto YouTube".
- Nhập Google Client ID & Secret để kết nối kênh và bật công tắc Auto-Pilot.

============================================================
Chúc bạn tạo ra nhiều video triệu view!
"""
    with open(RELEASE_DIR / "Huong_Dan_Su_Dung.txt", "w", encoding="utf-8") as f:
        f.write(huong_dan)

    # 7. Nen thanh file ZIP de gui cho ban be
    zip_path = BASE_DIR / "Ban_Clean_Chia_Se" / "AudioStoryStudio_Clean_v1.0.zip"
    print(f"[*] Dang nen file ZIP de chia se: {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(RELEASE_DIR):
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(RELEASE_DIR)
                zipf.write(file_path, rel_path)

    print("\n" + "=" * 60)
    print(" [OK] DA TAO THANH CONG BAN RELEASE CLEAN!")
    print(f" 1. Thu muc: {RELEASE_DIR}")
    print(f" 2. File ZIP de gui cho ban be: {zip_path}")
    print("=" * 60)

if __name__ == "__main__":
    create_clean_package()
