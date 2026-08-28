import asyncio
import os
import re
import uuid
import random
import subprocess
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import secrets
import base64
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel

from backend.config import (
    BASE_DIR, FRONTEND_DIR, OUTPUT_DIR, TEMP_DIR, BGM_DIR,
    TTS_VOICES, VISUAL_STYLES, ASPECT_RATIOS, load_settings, save_settings
)
from backend.tts_engine import tts_engine
from backend.story_engine import story_engine
from backend.visual_engine import visual_engine
from backend.audio_engine import audio_engine
from backend.render_engine import render_engine
from backend.youtube_engine import youtube_engine
from backend.scheduler import auto_scheduler

app = FastAPI(title="AI Audio Story Video Studio API")

@app.middleware("http")
async def basic_auth_middleware(request: Request, call_next):
    # Cho phép Google OAuth callback đi qua mà không bị chặn
    if request.url.path == "/api/youtube/oauth2callback":
        return await call_next(request)

    settings = load_settings()
    auth_enabled = settings.get("auth_enabled", True)
    if not auth_enabled:
        return await call_next(request)

    expected_username = str(settings.get("auth_username", "admin")).strip() or "admin"
    expected_password = str(settings.get("auth_password", "admin123")).strip() or "admin123"

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        return Response(
            content="Authentication Required. Please enter username and password.",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="AI Audio Story Studio"'}
        )

    try:
        encoded_creds = auth_header.split(" ", 1)[1]
        decoded = base64.b64decode(encoded_creds).decode("utf-8")
        username, _, password = decoded.partition(":")

        is_correct_user = secrets.compare_digest(username.strip(), expected_username)
        is_correct_pass = secrets.compare_digest(password.strip(), expected_password)

        if not (is_correct_user and is_correct_pass):
            return Response(
                content="Unauthorized: Sai tên đăng nhập hoặc mật khẩu.",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="AI Audio Story Studio"'}
            )
    except Exception:
        return Response(
            content="Invalid Authorization header",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="AI Audio Story Studio"'}
        )

    return await call_next(request)

@app.on_event("startup")
async def app_startup():
    auto_scheduler.start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Quản lý tiến trình render jobs
active_jobs: Dict[str, Dict[str, Any]] = {}

# Pydantic Schemas
class SettingsModel(BaseModel):
    api_key: Optional[str] = ""
    base_url: Optional[str] = "https://api.openai.com/v1"
    chat_model: Optional[str] = "gpt-4o-mini"
    image_model: Optional[str] = "dall-e-3"
    image_provider: Optional[str] = "pollinations"
    auth_enabled: Optional[bool] = True
    auth_username: Optional[str] = "admin"
    auth_password: Optional[str] = "admin123"

class StoryGenRequest(BaseModel):
    genre: str = "dark_mystery"
    topic: str = "Ngôi nhà cổ giữa rừng thông"
    target_minutes: int = 5
    num_scenes: Optional[int] = None

class ParseTextRequest(BaseModel):
    text: str
    style: str = "dark_mystery"

class TTSPreviewRequest(BaseModel):
    text: str
    voice: str = "vi-VN-HoaiMyNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"

class ImagePreviewRequest(BaseModel):
    prompt: str
    style: str = "dark_mystery"
    aspect_ratio: str = "16:9"

class SceneItem(BaseModel):
    scene: int
    text: str
    image_prompt: str

class ThumbnailGenRequest(BaseModel):
    title: str
    genre: Optional[str] = "dark_mystery"
    topic: Optional[str] = ""
    custom_prompt: Optional[str] = None
    style: Optional[str] = "dark_mystery"
    aspect_ratio: Optional[str] = "16:9"

class DescriptionGenRequest(BaseModel):
    title: str
    genre: Optional[str] = "dark_mystery"
    topic: Optional[str] = ""
    scenes: Optional[List[Dict[str, Any]]] = None

class RenderVideoRequest(BaseModel):
    title: str = "Truyện Audio Đặc Sắc"
    channel_name: str = "@TruyenAudioAI"
    scenes: List[SceneItem]
    voice: str = "vi-VN-HoaiMyNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    style: str = "dark_mystery"
    aspect_ratio: str = "16:9"
    bgm_name: Optional[str] = "ambient_mystery.mp3"
    bgm_volume: float = 0.15
    enable_waveform: bool = True

class YouTubeCredentialsRequest(BaseModel):
    client_id: str
    client_secret: str

class YouTubeAuthCodeRequest(BaseModel):
    auth_code: str

class YouTubeUploadManualRequest(BaseModel):
    video_filename: str
    title: str
    description: str
    tags: Optional[List[str]] = None
    privacy_status: str = "unlisted"
    thumbnail_filename: Optional[str] = None

class SchedulerConfigRequest(BaseModel):
    enabled: bool = False
    scheduled_times: List[str] = ["08:00", "12:30", "19:30"]
    mode: str = "ai_auto"
    topic_queue: List[str] = []
    genre: str = "dark_mystery"
    duration: int = 5
    voice: str = "vi-VN-HoaiMyNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    bgm_name: Optional[str] = ""
    bgm_volume: float = 0.15
    aspect_ratio: str = "16:9"
    enable_waveform: bool = True
    auto_upload_youtube: bool = False
    privacy_status: str = "unlisted"

@app.get("/api/config")
async def get_app_config():
    """Lấy danh sách cấu hình, giọng đọc, styles và BGM có sẵn"""
    bgm_files = [f.name for f in BGM_DIR.glob("*.mp3")]
    return {
        "voices": TTS_VOICES,
        "styles": VISUAL_STYLES,
        "aspect_ratios": ASPECT_RATIOS,
        "bgm_list": bgm_files,
        "settings": load_settings()
    }

@app.get("/api/settings")
async def get_settings():
    """Lấy cấu hình API ChatGPT & DALL-E"""
    return load_settings()

@app.post("/api/settings")
async def update_settings(model: SettingsModel):
    """Cập nhật API Key & Custom Base URL"""
    saved = save_settings(model.model_dump())
    return {"status": "ok", "settings": saved}

@app.post("/api/story/generate")
async def api_generate_story(req: StoryGenRequest):
    """Tạo kịch bản truyện và prompt ảnh tự động bằng AI (hỗ trợ 5p, 15p, 30p, 45p)"""
    scenes = await story_engine.generate_story(
        genre=req.genre,
        topic=req.topic,
        target_minutes=req.target_minutes,
        num_scenes=req.num_scenes
    )
    return {"scenes": scenes}

@app.post("/api/story/parse")
async def api_parse_story(req: ParseTextRequest):
    """Phân tách text người dùng dán vào thành các Scenes"""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Vui lòng nhập nội dung truyện.")
    scenes = story_engine.parse_raw_text_to_scenes(
        raw_text=req.text,
        style_key=req.style
    )
    return {"scenes": scenes}

@app.post("/api/story/description")
async def api_generate_description(req: DescriptionGenRequest):
    """Tạo mô tả video YouTube chuẩn SEO: Hook, Tóm tắt, Chapters, Hashtags"""
    desc_data = await story_engine.generate_video_description(
        title=req.title,
        genre=req.genre or "dark_mystery",
        topic=req.topic or req.title,
        scenes=req.scenes
    )
    return {"status": "ok", "description": desc_data}

@app.post("/api/story/upload-file")
async def api_upload_story_file(file: UploadFile = File(...)):
    """Upload file truyện (.txt, .md) cho truyện dài nhiều chương"""
    try:
        content_bytes = await file.read()
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = content_bytes.decode("utf-8-sig", errors="ignore")
        return {"filename": file.filename, "text": text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi khi đọc file: {str(e)}")

@app.post("/api/preview/tts")
async def api_preview_tts(req: TTSPreviewRequest):
    """Nghe thử giọng đọc TTS của 1 đoạn ngắn"""
    preview_id = uuid.uuid4().hex[:8]
    out_audio = TEMP_DIR / f"preview_tts_{preview_id}.mp3"
    result = await tts_engine.generate_speech(
        text=req.text,
        output_audio_path=str(out_audio),
        voice=req.voice,
        rate=req.rate,
        pitch=req.pitch
    )
    return {
        "audio_url": f"/temp/{out_audio.name}",
        "duration": result["duration"]
    }

@app.post("/api/preview/image")
async def api_preview_image(req: ImagePreviewRequest):
    """Tạo & xem trước 1 ảnh AI theo prompt (DALL-E 3 hoặc Flux)"""
    preview_id = uuid.uuid4().hex[:8]
    out_img = TEMP_DIR / f"preview_img_{preview_id}.jpg"
    await visual_engine.generate_image(
        prompt=req.prompt,
        output_image_path=str(out_img),
        style_key=req.style,
        aspect_ratio=req.aspect_ratio
    )
    return {"image_url": f"/temp/{out_img.name}"}

@app.post("/api/thumbnail/generate")
async def api_generate_thumbnail(req: ThumbnailGenRequest):
    """Tạo mới hoặc tạo lại Thumbnail AI chuẩn YouTube Cinematic 8K với chữ 3D nghệ thuật"""
    thumb_id = f"thumb_{int(time.time())}_{uuid.uuid4().hex[:4]}"
    out_path = str(OUTPUT_DIR / f"{thumb_id}.jpg")
    
    await visual_engine.generate_ai_thumbnail(
        title=req.title,
        output_image_path=out_path,
        genre=req.genre or "dark_mystery",
        topic=req.topic or req.title,
        custom_prompt=req.custom_prompt,
        style_key=req.style or "dark_mystery",
        aspect_ratio=req.aspect_ratio or "16:9"
    )
    return {
        "status": "ok",
        "thumbnail_url": f"/output/{Path(out_path).name}",
        "filename": Path(out_path).name
    }

@app.post("/api/render")
async def api_start_render(req: RenderVideoRequest, background_tasks: BackgroundTasks):
    """Bắt đầu tác vụ render toàn bộ video trong background"""
    if not req.scenes:
        raise HTTPException(status_code=400, detail="Danh sách Scene không được để trống.")

    job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    active_jobs[job_id] = {
        "id": job_id,
        "status": "processing",
        "step": "Bắt đầu khởi tạo dự án...",
        "progress": 5,
        "video_url": None,
        "thumbnail_url": None,
        "error": None
    }

    background_tasks.add_task(process_render_pipeline, job_id, req)
    return {"job_id": job_id}

@app.get("/api/jobs/{job_id}")
async def api_get_job_status(job_id: str):
    """Kiểm tra tiến độ render của job (bảo lưu trạng thái ngay cả khi server restart)"""
    job = active_jobs.get(job_id)
    if not job:
        status_file = TEMP_DIR / job_id / "status.json"
        if status_file.exists():
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    job = json.load(f)
                    active_jobs[job_id] = job
            except Exception:
                pass

    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy tác vụ render.")
    return job

@app.post("/api/open-folder")
async def api_open_output_folder():
    """Mở thư mục output trên Windows Explorer"""
    try:
        os.startfile(str(OUTPUT_DIR))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- CÁC ENDPOINT YOUTUBE API & OAUTH 2.0 ---

@app.get("/api/youtube/credentials")
async def api_get_youtube_credentials():
    """Lấy thông tin Client ID & Secret đã lưu"""
    creds = youtube_engine.get_client_credentials()
    return {
        "client_id": creds.get("client_id", ""),
        "has_secret": bool(creds.get("client_secret"))
    }

@app.post("/api/youtube/credentials")
async def api_save_youtube_credentials(req: YouTubeCredentialsRequest):
    """Lưu Client ID & Secret Google Cloud"""
    youtube_engine.save_client_credentials(req.client_id, req.client_secret)
    return {"status": "ok", "auth_url": youtube_engine.get_auth_url(req.client_id)}

@app.get("/api/youtube/auth-url")
async def api_get_youtube_auth_url(redirect_uri: Optional[str] = None):
    """Lấy đường dẫn URL đăng nhập Google OAuth"""
    url = youtube_engine.get_auth_url(redirect_uri=redirect_uri)
    return {"auth_url": url}

@app.get("/api/youtube/oauth2callback")
async def api_youtube_oauth2callback(code: Optional[str] = None, error: Optional[str] = None):
    """Tự động nhận callback từ Google sau khi người dùng bấm Allow"""
    if error:
        return HTMLResponse(f"""
        <html>
        <body style="font-family: system-ui, sans-serif; text-align: center; padding: 50px; background: #0b0f19; color: #f87171;">
            <h2>❌ Đăng Nhập Thất Bại</h2>
            <p>Google báo lỗi: {error}</p>
        </body>
        </html>
        """)

    if not code:
        return HTMLResponse("""
        <html>
        <body style="font-family: system-ui, sans-serif; text-align: center; padding: 50px; background: #0b0f19; color: #f87171;">
            <h2>❌ Không tìm thấy Authorization Code</h2>
        </body>
        </html>
        """)

    try:
        await youtube_engine.exchange_code_for_token(code, redirect_uri="http://localhost:8000/api/youtube/oauth2callback")
        channel = await youtube_engine.get_channel_info()
        ch_title = channel.get("title", "Kênh YouTube")
        return HTMLResponse(f"""
        <html>
        <head><title>Kết Nối YouTube Thành Công</title></head>
        <body style="font-family: system-ui, -apple-system, sans-serif; text-align: center; padding: 60px 20px; background: #0b0f19; color: #f8fafc;">
            <div style="max-width: 480px; margin: 0 auto; background: #1e293b; padding: 36px; border-radius: 16px; border: 1px solid rgba(16,185,129,0.3); box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                <div style="font-size: 48px; margin-bottom: 16px;">🎉</div>
                <h2 style="color: #34d399; margin-bottom: 8px;">Liên Kết Kênh Thành Công!</h2>
                <p style="font-size: 16px; font-weight: 600; color: #38bdf8; margin-bottom: 16px;">{ch_title}</p>
                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 24px;">Hệ thống đã lưu quyền truy cập để tự động tải video và thumbnail lên kênh.</p>
                <button onclick="window.close()" style="background: #38bdf8; color: #0b0f19; border: none; padding: 10px 24px; border-radius: 9999px; font-weight: 700; cursor: pointer; font-size: 14px;">
                    Đóng Cửa Sổ Này
                </button>
            </div>
            <script>
                setTimeout(() => {{ window.close(); }}, 3000);
            </script>
        </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(f"""
        <html>
        <body style="font-family: system-ui, sans-serif; text-align: center; padding: 50px; background: #0b0f19; color: #f87171;">
            <h2>❌ Lỗi Đổi Token</h2>
            <p>{str(e)}</p>
        </body>
        </html>
        """)

@app.post("/api/youtube/auth-code")
async def api_exchange_youtube_auth_code(req: YouTubeAuthCodeRequest):
    """Gửi mã ủy quyền OAuth để lấy Token (Hỗ trợ cả mã code thô hoặc dán nguyên link URL callback)"""
    raw_code = req.auth_code.strip()
    if "code=" in raw_code:
        import urllib.parse
        try:
            parsed = urllib.parse.urlparse(raw_code)
            qs = urllib.parse.parse_qs(parsed.query)
            if "code" in qs:
                raw_code = qs["code"][0]
            else:
                raw_code = raw_code.split("code=")[1].split("&")[0]
        except Exception:
            if "code=" in raw_code:
                raw_code = raw_code.split("code=")[1].split("&")[0]

    try:
        await youtube_engine.exchange_code_for_token(raw_code)
        channel = await youtube_engine.get_channel_info()
        return {"status": "ok", "channel": channel}
    except Exception as e:
        try:
            await youtube_engine.exchange_code_for_token(raw_code, redirect_uri="urn:ietf:wg:oauth:2.0:oob")
            channel = await youtube_engine.get_channel_info()
            return {"status": "ok", "channel": channel}
        except Exception:
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/youtube/status")
async def api_get_youtube_status():
    """Kiểm tra trạng thái kết nối Kênh YouTube"""
    return await youtube_engine.get_channel_info()

@app.post("/api/youtube/disconnect")
async def api_disconnect_youtube():
    """Hủy liên kết Kênh YouTube"""
    youtube_engine.disconnect_channel()
    return {"status": "ok"}

@app.post("/api/youtube/upload-manual")
async def api_manual_upload_youtube(req: YouTubeUploadManualRequest):
    """Upload thủ công một video có sẵn trong output lên YouTube"""
    video_path = str(OUTPUT_DIR / req.video_filename)
    thumb_path = str(OUTPUT_DIR / req.thumbnail_filename) if req.thumbnail_filename else None
    
    try:
        res = await youtube_engine.upload_video_to_youtube(
            video_path=video_path,
            title=req.title,
            description=req.description,
            tags=req.tags,
            privacy_status=req.privacy_status,
            thumbnail_path=thumb_path
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- CÁC ENDPOINT LÊN LỊCH TỰ ĐỘNG (SCHEDULER) ---

@app.get("/api/scheduler/config")
async def api_get_scheduler_config():
    """Lấy cấu hình Lên lịch sản xuất"""
    return auto_scheduler.load_config()

@app.post("/api/scheduler/config")
async def api_save_scheduler_config(req: SchedulerConfigRequest):
    """Lưu cấu hình Lên lịch sản xuất"""
    saved = auto_scheduler.save_config(req.model_dump())
    return {"status": "ok", "config": saved}

@app.get("/api/scheduler/history")
async def api_get_scheduler_history():
    """Lấy danh sách nhật ký các video đã sản xuất & upload"""
    return auto_scheduler.load_history()

@app.post("/api/scheduler/trigger-now")
async def api_trigger_scheduler_now(background_tasks: BackgroundTasks):
    """Chạy ngay lập tức 1 quy trình Auto-Pilot theo cấu hình hiện tại"""
    if auto_scheduler.current_running_job:
        raise HTTPException(status_code=400, detail="Đang có một tiến trình Auto-Pilot chạy ngầm. Vui lòng đợi hoàn thành.")
    
    background_tasks.add_task(auto_scheduler.execute_autopilot_pipeline, "Chạy thủ công ngay")
    return {"status": "started", "message": "Đã khởi động quy trình Auto-Pilot thành công."}

async def process_render_pipeline(job_id: str, req: RenderVideoRequest):
    """Quy trình tự động hóa tốc độ cao (song song đa luồng) xuất Video truyện Audio + Thumbnail AI"""
    import concurrent.futures
    job = active_jobs[job_id]
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    def save_state():
        try:
            with open(job_dir / "status.json", "w", encoding="utf-8") as f:
                json.dump(job, f, ensure_ascii=False)
        except Exception:
            pass

    save_state()

    try:
        total_scenes = len(req.scenes)

        # BƯỚC 1: Tạo TTS & Subtitles SONG SONG (Tối đa 5 luồng đồng thời)
        job["step"] = f"Đang chuyển đổi giọng đọc (TTS) & phụ đề song song cho {total_scenes} phân cảnh..."
        job["progress"] = 15
        save_state()

        sem_tts = asyncio.Semaphore(5)
        completed_tts = 0

        async def run_single_tts(idx, sc):
            nonlocal completed_tts
            audio_path = str(job_dir / f"voice_sc_{sc.scene}.mp3")
            srt_path = str(job_dir / f"sub_sc_{sc.scene}.srt")
            async with sem_tts:
                res = await tts_engine.generate_speech(
                    text=sc.text,
                    output_audio_path=audio_path,
                    output_srt_path=srt_path,
                    voice=req.voice,
                    rate=req.rate,
                    pitch=req.pitch
                )
                completed_tts += 1
                job["progress"] = 15 + int(completed_tts / total_scenes * 20)
                return idx, audio_path, (srt_path, res["duration"], sc.text)

        tts_tasks = [run_single_tts(i, sc) for i, sc in enumerate(req.scenes)]
        tts_results = await asyncio.gather(*tts_tasks)
        tts_results.sort(key=lambda x: x[0])

        scene_audio_files = [r[1] for r in tts_results]
        scene_srt_files = [r[2] for r in tts_results]

        # BƯỚC 2: Tạo Hình ảnh AI (Tuần tự an toàn 1 luồng tránh nghẽn Proxy kèm Khóa Seed Đồng Bộ)
        job["step"] = f"Đang tạo hình ảnh AI cho {total_scenes} phân cảnh qua Proxy..."
        job["progress"] = 35

        sem_img = asyncio.Semaphore(1)
        completed_img = 0
        master_seed = random.randint(100000, 999999) # Khóa Seed nghệ thuật đồng bộ toàn bộ video

        async def run_single_image(idx, sc):
            nonlocal completed_img
            img_path = str(job_dir / f"img_sc_{sc.scene}.jpg")
            async with sem_img:
                job["step"] = f"Đang tạo hình ảnh AI phân cảnh {completed_img + 1}/{total_scenes}..."
                await visual_engine.generate_image(
                    prompt=sc.image_prompt,
                    output_image_path=img_path,
                    style_key=req.style,
                    aspect_ratio=req.aspect_ratio,
                    seed=master_seed
                )
                completed_img += 1
                job["progress"] = 35 + int(completed_img / total_scenes * 20)
                return idx, img_path

        img_tasks = [run_single_image(i, sc) for i, sc in enumerate(req.scenes)]
        img_results = await asyncio.gather(*img_tasks)
        img_results.sort(key=lambda x: x[0])
        scene_images = [r[1] for r in img_results]

        # BƯỚC 3: Áp dụng hiệu ứng chuyển động Ken Burns ĐA LUỒNG CPU
        job["step"] = f"Đang render hiệu ứng chuyển động camera đa luồng CPU cho {total_scenes} clips..."
        job["progress"] = 55

        loop = asyncio.get_running_loop()
        completed_clips = 0
        max_workers = min(4, os.cpu_count() or 2)

        def render_clip_sync(idx, img_p, sc_dur):
            nonlocal completed_clips
            clip_path = str(job_dir / f"clip_sc_{idx+1}.mp4")
            visual_engine.create_ken_burns_video(
                image_path=img_p,
                output_video_path=clip_path,
                duration=sc_dur,
                aspect_ratio=req.aspect_ratio
            )
            completed_clips += 1
            job["progress"] = 55 + int(completed_clips / total_scenes * 15)
            return idx, clip_path

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = [
                loop.run_in_executor(executor, render_clip_sync, idx, img_p, sc_dur)
                for idx, (img_p, (_, sc_dur, _)) in enumerate(zip(scene_images, scene_srt_files))
            ]
            clip_results = await asyncio.gather(*tasks)
            clip_results.sort(key=lambda x: x[0])
            scene_video_clips = [r[1] for r in clip_results]

        # BƯỚC 4: Ghép nối Video nền & Trộn Âm thanh
        job["step"] = "Đang ghép nối video & hòa âm nhạc nền (BGM)..."
        job["progress"] = 72

        base_video_path = str(job_dir / "base_video.mp4")
        render_engine.concat_scene_videos(scene_video_clips, base_video_path)

        full_voice_path = str(job_dir / "full_voice.mp3")
        audio_engine.concat_audio_files(scene_audio_files, full_voice_path)

        bgm_path = str(BGM_DIR / req.bgm_name) if req.bgm_name else None
        mixed_audio_path = str(job_dir / "mixed_audio.mp3")
        audio_engine.mix_voice_and_bgm(
            voice_path=full_voice_path,
            output_path=mixed_audio_path,
            bgm_path=bgm_path,
            bgm_volume=req.bgm_volume
        )

        full_srt_path = str(job_dir / "full_subtitles.srt")
        _combine_srt_files(scene_srt_files, full_srt_path)

        # BƯỚC 5: Xuất Video thành phẩm (Waveform + Subtitle + Watermark)
        job["step"] = "Đang kết xuất video 1080p với sóng âm & phụ đề..."
        job["progress"] = 85

        safe_title = re.sub(r'[\\/:*?"<>|]', '_', req.title).strip() or "video_truyen"
        final_filename = f"video_{int(time.time())}.mp4"
        final_video_path = str(OUTPUT_DIR / final_filename)

        render_engine.composite_final_video(
            base_video_path=base_video_path,
            audio_path=mixed_audio_path,
            output_path=final_video_path,
            srt_subtitles_path=full_srt_path,
            title_text=req.title,
            watermark_text=req.channel_name,
            enable_waveform=req.enable_waveform,
            aspect_ratio=req.aspect_ratio
        )

        # BƯỚC 6: Tạo Thumbnail YouTube AI Chuẩn Cinematic Đỉnh Cao
        job["step"] = "Đang tạo Thumbnail YouTube AI chuẩn điện ảnh 8K..."
        job["progress"] = 92
        thumb_filename = f"thumb_{int(time.time())}.jpg"
        final_thumb_path = str(OUTPUT_DIR / thumb_filename)

        await visual_engine.generate_ai_thumbnail(
            title=req.title,
            output_image_path=final_thumb_path,
            genre=req.style,
            topic=req.title,
            style_key=req.style,
            aspect_ratio=req.aspect_ratio
        )

        # BƯỚC 7: Tự Động Soạn Thảo Mô Tả YouTube Chuẩn SEO & Hashtags
        job["step"] = "Đang soạn thảo Mô tả Video & Hashtags chuẩn SEO..."
        job["progress"] = 98

        desc_data = await story_engine.generate_video_description(
            title=req.title,
            genre=req.style,
            topic=req.title,
            scenes=[sc.model_dump() for sc in req.scenes]
        )

        job["progress"] = 100
        job["status"] = "completed"
        job["step"] = "Hoàn thành! Video, Thumbnail AI và Mô tả SEO đã sẵn sàng."
        job["video_url"] = f"/output/{final_filename}"
        job["thumbnail_url"] = f"/output/{thumb_filename}"
        job["description"] = desc_data
        save_state()

    except Exception as e:
        import traceback
        traceback.print_exc()
        job["status"] = "error"
        job["error"] = str(e)
        job["step"] = f"Lỗi trong quá trình render: {str(e)}"
        save_state()

def _combine_srt_files(scene_srt_info: List[tuple], output_full_srt: str):
    """Kết hợp các file SRT từng scene thành 1 file SRT chuẩn duy nhất theo timeline tích lũy"""
    from backend.tts_engine import format_timestamp_srt
    
    combined_subs = []
    current_time_offset = 0.0
    sub_counter = 1

    for srt_path, duration, text in scene_srt_info:
        if os.path.exists(srt_path):
            with open(srt_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            blocks = content.split("\n\n") if content else []
            for block in blocks:
                lines = block.strip().split("\n")
                if len(lines) >= 3:
                    time_line = lines[1]
                    sub_text = "\n".join(lines[2:])
                    match = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})", time_line)
                    if match:
                        h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())
                        start_sec = h1*3600 + m1*60 + s1 + ms1/1000.0 + current_time_offset
                        end_sec = h2*3600 + m2*60 + s2 + ms2/1000.0 + current_time_offset
                        
                        combined_subs.append(
                            f"{sub_counter}\n{format_timestamp_srt(start_sec)} --> {format_timestamp_srt(end_sec)}\n{sub_text}"
                        )
                        sub_counter += 1
        
        current_time_offset += duration

    with open(output_full_srt, "w", encoding="utf-8") as f:
        f.write("\n\n".join(combined_subs) + "\n")

# Mount Static Files
app.mount("/temp", StaticFiles(directory=str(TEMP_DIR)), name="temp")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
