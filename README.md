# 🎬 AudioStory Studio AI — Hệ Thống Tự Động Hóa Sản Xuất Video Truyện Audio & YouTube Auto-Pilot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Ready-green?style=for-the-badge&logo=ffmpeg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20VPS-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)

**Giải pháp toàn diện ứng dụng Trí Tuệ Nhân Tạo (AI) để tự động hóa 100% quy trình sản xuất Video Truyện Audio: từ viết cốt truyện, thu âm giọng đọc truyền cảm, vẽ tranh minh họa phân cảnh, dựng phim chuyển động Ken Burns, tạo sóng nhạc Waveform, thiết kế Thumbnail AI cho đến tự động đăng tải lên Kênh YouTube.**

</div>

---

## ✨ Tính Năng Nổi Bật

### 🧠 1. Biên Soạn Cốt Truyện AI Đa Thể Loại
* Hỗ trợ đa dạng thể loại: **Kinh dị (Dark Mystery)**, **Tổng tài / CEO Drama**, **Trinh thám**, **Tiên hiệp / Trùng sinh**, **Lofi Tâm sự**, **Cổ tích / Thần thoại**,...
* Tự động chia mạch truyện thành các phân cảnh logic có lời thoại và mô tả hình ảnh chi tiết.
* Tích hợp **OpenAI GPT-4o / GPT-4o-mini**, hỗ trợ tuỳ biến Proxy API và kịch bản mẫu linh hoạt.

### 🎙️ 2. Lồng Tiếng AI Truyền Cảm (Edge-TTS Siêu Tốc)
* Giọng đọc tiếng Việt chất lượng cao từ Microsoft Edge Neural: `Hoài My (Nữ)`, `Nam Minh (Nam)`...
* Tùy chỉnh tốc độ đọc (Rate) và cao độ (Pitch).
* Tự động đồng bộ thời lượng giọng đọc với từng phân cảnh và tự động sinh phụ đề chuẩn SRT.

### 🎨 3. Vẽ Tranh Minh Họa AI Phân Cảnh (8K Cinematic)
* Tự động tạo câu lệnh (Prompt) điện ảnh theo sát ngữ cảnh của từng đoạn truyện.
* Hỗ trợ **Pollinations AI (Flux / Turbo)** hoàn toàn miễn phí & **OpenAI DALL-E 3 / Proxy SD**.
* Tự động chuẩn hóa kích thước, tỉ lệ vàng (16:9 cho YouTube ngang hoặc 9:16 cho Shorts/TikTok).

### 🎬 4. Dựng Phim Điện Ảnh Tự Động (FFmpeg Engine)
* Áp dụng hiệu ứng chuyển động **Ken Burns** (Zoom In, Zoom Out, Pan Left/Right) mượt mà 25-30fps.
* Tự động mix **Nhạc nền BGM** theo thể loại với cơ chế chống lấn át giọng đọc (Audio Ducking).
* Tích hợp **Sóng âm Audio Waveform** động và chèn phụ đề tự động (Burned Subtitles).

### 🖼️ 5. Thiết Kế Thumbnail AI 3D & Viết Mô Tả Chuẩn SEO
* Tự động vẽ **Hình thu nhỏ (Thumbnail)** chuẩn YouTube 1280x720 với chữ 3D nghệ thuật bắt mắt (High CTR).
* Tối ưu hóa dung lượng ảnh (< 1.5MB) và chuẩn màu RGB JPEG tương thích 100% với YouTube API.
* Tự động viết tiêu đề giật tít, mô tả chi tiết và bộ thẻ Tags SEO thịnh hành.

### 🚀 6. Chế Độ Lên Lịch Tự Động Hoàn Toàn (Auto-Pilot 24/7)
* Cài đặt các khung giờ vàng đăng bài trong ngày (ví dụ: `08:00`, `12:30`, `19:30`).
* Tự động lấy chủ đề từ danh sách hàng đợi (Queue) hoặc để AI tự sáng tạo đề tài mới.
* Tự động tải video lên Kênh YouTube qua **Google YouTube Data API v3** (hỗ trợ Public, Unlisted, Private hoặc Hẹn giờ công chiếu).

---

## 🖥️ Giao Diện Ứng Dụng

* **Web Studio Hiện Đại**: Thiết kế theo phong cách Dark Mode Glassmorphism, hiển thị trực quan tiến trình thời gian thực, xem trước video và tải file trực tiếp.
* **Bản Desktop App (.EXE)**: Đóng gói gọn gàng, khởi động nhanh trên Windows mà không cần mở trình duyệt.

---

## 🛠️ Yêu Cầu Hệ Thống

* **Hệ điều hành**: Windows 10/11, Linux (Ubuntu 20.04+, Debian, CentOS), macOS.
* **Python**: Phiên bản `3.8` trở lên.
* **FFmpeg**: Đã cài đặt và có trong biến môi trường `PATH`.

---

## 📦 Hướng Dẫn Cài Đặt & Chạy

### 1. Cách 1: Chạy trên Windows

**Bước 1: Clone dự án về máy**
```bash
git clone https://github.com/davidthuong/truyen-audio.git
cd truyen-audio
```

**Bước 2: Cài đặt thư viện**
```bash
pip install -r requirements.txt
```

**Bước 3: Khởi động nhanh**
* Nhấp đúp chuột vào file `run.bat` để mở Web Studio.
* Hoặc chạy giao diện Desktop: nhấp đúp vào file `Chay_App_Desktop.bat` (hoặc `AudioStoryStudio.exe`).

---

### 2. Cách 2: Chạy trên Linux VPS / Server (Treo Auto-Pilot 24/7)

**Bước 1: Cài đặt Python, FFmpeg và Font chữ trên Linux**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg fonts-dejavu git
```

**Bước 2: Clone repository & cài đặt packages**
```bash
git clone https://github.com/davidthuong/truyen-audio.git
cd truyen-audio
pip install -r requirements.txt
```

**Bước 3: Khởi động Web Server**
```bash
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```
> *Mở trình duyệt truy cập: `http://<IP-VPS>:8000` để sử dụng.*

**Bước 4: Treo máy chạy ngầm 24/7 (Background Daemon)**
```bash
nohup python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

---

## 📂 Cấu Trúc Thư Mục Dự Án

```text
truyen-audio/
│
├── backend/                  # Mã nguồn Backend FastAPI & Các Engine AI
│   ├── app.py                # REST API & WebSocket Server
│   ├── config.py             # Cấu hình phong cách, giọng đọc, tỉ lệ khung hình
│   ├── story_engine.py       # Engine sáng tạo cốt truyện & kịch bản phân cảnh
│   ├── tts_engine.py         # Engine lồng tiếng thuyết minh Edge-TTS
│   ├── visual_engine.py      # Engine vẽ tranh AI & tạo Thumbnail
│   ├── audio_engine.py       # Engine xử lý âm thanh & mix nhạc nền BGM
│   ├── render_engine.py      # Engine FFmpeg dựng video Ken Burns & Waveform
│   ├── youtube_engine.py     # Engine liên kết OAuth & Tải video lên YouTube
│   └── scheduler.py          # Bộ lập lịch Auto-Pilot chạy ngầm theo giờ
│
├── frontend/                 # Giao diện người dùng Web Studio (HTML/CSS/JS)
│   ├── css/style.css         # Giao diện Dark Glassmorphism hiện đại
│   ├── js/app.js             # Logic kết nối API & điều khiển giao diện
│   └── index.html            # Trang điều khiển chính
│
├── assets/                   # Kho tài nguyên dùng chung
│   └── bgm/                  # Nhạc nền miễn phí bản quyền (Cinematic, Lofi, Horror)
│
├── desktop_app.py            # Khởi chạy Desktop App với PyWebView
├── Tao_Ban_Clean.py          # Script tạo bản phân phối sạch không lộ tài khoản
├── Dong_Goi_EXE.bat          # Script đóng gói thành 1 file .EXE duy nhất
├── run.bat                   # File khởi động nhanh trên Windows
├── requirements.txt          # Danh sách thư viện Python phụ thuộc
└── README.md                 # Tài liệu hướng dẫn sử dụng
```

---

## 🔑 Thiết Lập API & Liên Kết Kênh YouTube

1. **OpenAI / Proxy API**:
   * Nhấn nút **"⚙️ Cài Đặt API"** trên giao diện web hoặc nhập trực tiếp vào file `settings.json`.
   * Hỗ trợ OpenAI API Key chuẩn hoặc bất kỳ Proxy AI tương thích định dạng `/v1/chat/completions` & `/v1/images/generations`.
   * *Nếu không nhập API Key, hệ thống vẫn hoạt động bình thường với mô hình AI miễn phí.*

2. **Google YouTube Data API v3**:
   * Tạo dự án trên [Google Cloud Console](https://console.cloud.google.com/), kích hoạt **YouTube Data API v3**.
   * Tạo OAuth 2.0 Client ID (chọn loại Desktop App hoặc Web App).
   * Dán `Client ID` & `Client Secret` vào tab **"Lên Lịch & Auto YouTube"** và bấm **"Đăng Nhập Kênh YouTube"**.

---

## 📜 Giấy Phép (License)

Dự án được phân phối dưới giấy phép **MIT License**. Bạn được toàn quyền sử dụng, chỉnh sửa và triển khai cho mục đích cá nhân hoặc thương mại.

---

<div align="center">
⭐ <i>Nếu bạn thấy dự án hữu ích, hãy tặng 1 ngôi sao (Star) trên GitHub để ủng hộ tác giả nhé!</i> ⭐
</div>
