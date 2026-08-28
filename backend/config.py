import os
import json
from pathlib import Path
from typing import Dict, Any

import sys

# Thư mục gốc dự án (Hỗ trợ cả môi trường Dev và khi đóng gói file .EXE)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
    # Nếu chạy onedir/onefile, trỏ frontend và assets vào bundle
    BUNDLE_DIR = Path(getattr(sys, '_MEIPASS', BASE_DIR))
    FRONTEND_DIR = BUNDLE_DIR / "frontend"
    ASSETS_DIR = BUNDLE_DIR / "assets"
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    FRONTEND_DIR = BASE_DIR / "frontend"
    ASSETS_DIR = BASE_DIR / "assets"

BACKEND_DIR = BASE_DIR / "backend"
FONTS_DIR = ASSETS_DIR / "fonts"
BGM_DIR = ASSETS_DIR / "bgm"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
SETTINGS_FILE = BASE_DIR / "settings.json"

for path in [FONTS_DIR, BGM_DIR, OUTPUT_DIR, TEMP_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Tự động lấy OPENAI_API_KEY từ biến môi trường hệ thống nếu có
ENV_API_KEY = os.environ.get("OPENAI_API_KEY", "")

DEFAULT_SETTINGS = {
    "api_key": ENV_API_KEY,
    "base_url": "http://103.238.213.17:8317/v1",
    "chat_model": "gpt-4o-mini",
    "image_model": "gpt-image-2",
    "image_provider": "openai_dalle",
    "default_voice": "vi-VN-HoaiMyNeural",
    "default_bgm_volume": 0.15,
    "auth_enabled": True,
    "auth_username": "admin",
    "auth_password": "admin123",
    "tts_provider": "edge_tts",
    "vivibe_api_key": "",
    "vivibe_voice_id": "",
    "vivibe_speed": 1.0
}

def load_settings() -> Dict[str, Any]:
    current = dict(DEFAULT_SETTINGS)
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                current.update(data)
        except Exception:
            pass
    # Nếu trong settings chưa có api_key mà môi trường có thì lấy từ môi trường
    if not current.get("api_key") and ENV_API_KEY:
        current["api_key"] = ENV_API_KEY
    return current

def save_settings(new_settings: Dict[str, Any]) -> Dict[str, Any]:
    current = load_settings()
    current.update(new_settings)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=4, ensure_ascii=False)
    return current

# Danh sách giọng đọc Edge-TTS Tiếng Việt chất lượng cao
TTS_VOICES = [
    {
        "id": "vi-VN-HoaiMyNeural",
        "name": "Hoài My (Nữ - Truyền cảm, tâm sự, truyền thanh)",
        "gender": "Female",
        "default": True
    },
    {
        "id": "vi-VN-NamMinhNeural",
        "name": "Nam Minh (Nam - Trầm ấm, kiếm hiệp, trinh thám, kinh dị)",
        "gender": "Male",
        "default": False
    },
    {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher (English - Deep Male)",
        "gender": "Male",
        "default": False
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny (English - Natural Female)",
        "gender": "Female",
        "default": False
    }
]

# Các Preset Phong cách Visual (Image Style Prompts)
VISUAL_STYLES = {
    "ceo_drama": {
        "name": "Tổng Tài / Thương Trường / Trả Thù (CEO & Corporate Drama)",
        "prompt_suffix": "cinematic Asian corporate drama movie still, handsome young Asian male CEO in luxury tailored black suit, high-end skyscraper penthouse office at night, modern glass reflections, high tension, shot on 35mm lens, photorealistic 8k, blockbuster color grading, masterpiece",
        "negative_prompt": "cartoon, lofi, anime watercolor, ugly, casual clothing, bad anatomy, blurry"
    },
    "dark_mystery": {
        "name": "Kinh dị / Bí ẩn (Dark Mystery & Creepypasta)",
        "prompt_suffix": "dark cinematic atmosphere, eerie moody lighting, mist, volumetric fog, dramatic shadows, photorealistic, 8k resolution, cinematic composition, mystery novel aesthetic, masterpiece",
        "negative_prompt": "cartoon, bright, oversaturated, low quality, blurry, text, watermark"
    },
    "ancient_fantasy": {
        "name": "Tiên hiệp / Kiếm hiệp / Cổ trang (Ancient Fantasy)",
        "prompt_suffix": "ancient asian fantasy, wuxia xianxia style, ethereal mountains, mystical mist, traditional hanfu/ao dai, glowing particles, detailed digital painting, artstation trending, 8k",
        "negative_prompt": "modern, futuristic, western, low quality, distorted, bad anatomy"
    },
    "romantic_lofi": {
        "name": "Tâm sự / Lofi / Ngôn tình (Emotional & Lofi Vibe)",
        "prompt_suffix": "aesthetic anime watercolor style, soft pastel lighting, cozy room, rain on window, emotional nostalgic vibe, Makoto Shinkai style, lofi hip hop aesthetic, high detail",
        "negative_prompt": "dark, horror, ugly, deformed, blurry, pixelated"
    },
    "cinematic_realistic": {
        "name": "Điện ảnh / Hiện đại (Cinematic Ultra-Realistic)",
        "prompt_suffix": "cinematic movie still, 35mm photograph, shot on Arri Alexa, beautiful volumetric light, color graded, shallow depth of field, 8k uhd, photorealistic details",
        "negative_prompt": "illustration, 3d render, plastic, oversaturated, deformed"
    },
    "anime_story": {
        "name": "Anime Nhật Bản (Japanese Anime Art)",
        "prompt_suffix": "high quality anime artwork, vibrant colors, detailed scenery, studio ghibli and kyoto animation inspired, breathtaking background, 4k",
        "negative_prompt": "photorealistic, 3d, dark, muddy colors, bad hands"
    }
}

# Các tỉ lệ khung hình hỗ trợ
ASPECT_RATIOS = {
    "16:9": {
        "name": "YouTube Ngang (1920x1080 - 16:9)",
        "width": 1920,
        "height": 1080
    },
    "9:16": {
        "name": "YouTube Shorts / TikTok (1080x1920 - 9:16)",
        "width": 1080,
        "height": 1920
    }
}
