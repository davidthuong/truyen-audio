import os
import re
import json
import time
import random
import datetime
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.config import BASE_DIR, OUTPUT_DIR, TEMP_DIR, BGM_DIR, load_settings
from backend.story_engine import story_engine
from backend.tts_engine import tts_engine
from backend.visual_engine import visual_engine
from backend.audio_engine import audio_engine
from backend.render_engine import render_engine
from backend.youtube_engine import youtube_engine

def safe_log(msg: Any):
    """Ghi log an toàn tránh lỗi UnicodeEncodeError trên Windows"""
    try:
        print(f"[AutoScheduler] {msg}")
    except UnicodeEncodeError:
        try:
            print(f"[AutoScheduler] {str(msg).encode('ascii', 'replace').decode('ascii')}")
        except Exception:
            pass

SCHEDULER_CONFIG_FILE = BASE_DIR / "scheduler_config.json"
UPLOAD_HISTORY_FILE = BASE_DIR / "upload_history.json"

DEFAULT_SCHEDULER_CONFIG = {
    "enabled": False,
    "scheduled_times": ["08:00", "12:30", "19:30"],
    "mode": "ai_auto",  # 'ai_auto' hoặc 'queue'
    "topic_queue": [
        "3 năm sau, tôi trở về thâu tóm công ty của kẻ phản bội",
        "Bí mật gia tộc tài phiệt bị lãng quên trong màn đêm",
        "Cuộc điện thoại bí ẩn lúc 2 giờ sáng từ quá khứ"
    ],
    "genre": "dark_mystery",
    "duration": 5,
    "voice": "vi-VN-HoaiMyNeural",
    "rate": "+0%",
    "pitch": "+0Hz",
    "bgm_name": "",
    "bgm_volume": 0.15,
    "aspect_ratio": "16:9",
    "enable_waveform": True,
    "auto_upload_youtube": False,
    "privacy_status": "unlisted",  # public, unlisted, private
    "last_run_date": "",
    "executed_slots_today": []
}

class AutoScheduler:
    def __init__(self):
        self.is_running = False
        self.current_running_job = None
        self._task = None

    def load_config(self) -> Dict[str, Any]:
        """Tải cấu hình Lên lịch từ file"""
        config = dict(DEFAULT_SCHEDULER_CONFIG)
        if SCHEDULER_CONFIG_FILE.exists():
            try:
                with open(SCHEDULER_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    config.update(data)
            except Exception:
                pass
        return config

    def save_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Lưu cấu hình Lên lịch"""
        config = self.load_config()
        config.update(new_config)
        with open(SCHEDULER_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return config

    def load_history(self) -> List[Dict[str, Any]]:
        """Tải danh sách lịch sử sản xuất & upload"""
        if UPLOAD_HISTORY_FILE.exists():
            try:
                with open(UPLOAD_HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def append_history(self, record: Dict[str, Any]):
        """Thêm một bản ghi mới vào lịch sử"""
        history = self.load_history()
        history.insert(0, record)
        history = history[:100]  # Giữ lại 100 video gần nhất
        with open(UPLOAD_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def start(self):
        """Bắt đầu vòng lặp kiểm tra lịch chạy ngầm"""
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._scheduler_loop())
            safe_log("Da kich hoat bo lap lich chay ngam.")

    def stop(self):
        """Dừng bộ lập lịch"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
        safe_log("Da dung bo lap lich.")

    async def _scheduler_loop(self):
        """Vòng lặp kiểm tra thời gian mỗi 30 giây"""
        while self.is_running:
            try:
                await self._check_and_trigger()
            except Exception as e:
                safe_log(f"Loi kiem tra lich: {e}")
            await asyncio.sleep(30)

    async def _check_and_trigger(self):
        config = self.load_config()
        if not config.get("enabled", False):
            return

        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_time_str = now.strftime("%H:%M")

        # Reset danh sách slot đã chạy khi sang ngày mới
        if config.get("last_run_date") != today_str:
            config["last_run_date"] = today_str
            config["executed_slots_today"] = []
            self.save_config(config)

        scheduled_times = config.get("scheduled_times", [])
        executed_slots = config.get("executed_slots_today", [])

        for target_time in scheduled_times:
            if target_time == current_time_str and target_time not in executed_slots:
                if self.current_running_job is None:
                    safe_log(f"Dung gio len lich '{target_time}'! Bat dau quy trinh Auto-Pilot...")
                    executed_slots.append(target_time)
                    config["executed_slots_today"] = executed_slots
                    self.save_config(config)
                    asyncio.create_task(self.execute_autopilot_pipeline(source=f"Tự động ({target_time})"))
                break

    async def execute_autopilot_pipeline(self, source: str = "Thủ công") -> Dict[str, Any]:
        """Quy trình sản xuất trọn gói Auto-Pilot: Viết truyện -> Render -> Thumbnail -> SEO -> Upload YouTube"""
        config = self.load_config()
        history_record = {
            "id": f"auto_{int(time.time())}",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source,
            "title": "",
            "genre": config.get("genre", "dark_mystery"),
            "duration": config.get("duration", 5),
            "video_url": "",
            "thumbnail_url": "",
            "youtube_url": "",
            "youtube_status": "skipped",
            "status": "processing",
            "error": None
        }

        self.current_running_job = history_record["id"]
        job_dir = TEMP_DIR / history_record["id"]
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Chọn đề tài & thể loại (Hỗ trợ Xoay tua ngẫu nhiên & Gán tag [thể_loại] trong hàng đợi)
            import random
            available_genres = ["ceo_drama", "dark_mystery", "ancient_fantasy", "romantic_lofi", "cinematic_realistic", "anime_story"]
            selected_genre = config.get("genre", "dark_mystery")

            mode = config.get("mode", "ai_auto")
            queue = config.get("topic_queue", [])
            topic = ""

            if mode == "queue" and queue:
                raw_topic = queue.pop(0).strip()
                config["topic_queue"] = queue
                self.save_config(config)

                # Kiểm tra xem dòng có gắn tag [thể_loại] không
                tag_match = re.match(r"^\[(.*?)\]\s*(.*)", raw_topic, re.IGNORECASE)
                if tag_match:
                    tag_str = tag_match.group(1).lower().strip()
                    topic = tag_match.group(2).strip()

                    tag_mapping = {
                        "ceo_drama": "ceo_drama", "tổng tài": "ceo_drama", "thương trường": "ceo_drama", "trả thù": "ceo_drama",
                        "dark_mystery": "dark_mystery", "kinh dị": "dark_mystery", "bí ẩn": "dark_mystery", "creepypasta": "dark_mystery",
                        "romantic_lofi": "romantic_lofi", "lofi": "romantic_lofi", "ngôn tình": "romantic_lofi", "tâm sự": "romantic_lofi",
                        "ancient_fantasy": "ancient_fantasy", "tiên hiệp": "ancient_fantasy", "kiếm hiệp": "ancient_fantasy", "cổ trang": "ancient_fantasy",
                        "cinematic_realistic": "cinematic_realistic", "điện ảnh": "cinematic_realistic", "trinh thám": "cinematic_realistic",
                        "anime_story": "anime_story", "anime": "anime_story"
                    }
                    if tag_str in tag_mapping:
                        selected_genre = tag_mapping[tag_str]
                else:
                    topic = raw_topic
            else:
                if selected_genre == "random_all":
                    selected_genre = random.choice(available_genres)
                topic = f"Chuyện kịch tính thể loại {selected_genre} chưa từng được kể"

            if selected_genre == "random_all":
                selected_genre = random.choice(available_genres)

            history_record["title"] = topic
            history_record["genre"] = selected_genre

            # 2. Sinh kịch bản phân cảnh
            safe_log(f"Dang sinh kich ban ({selected_genre}) cho de tai: '{topic}'...")
            scenes = await story_engine.generate_story(
                genre=selected_genre,
                topic=topic,
                target_minutes=config.get("duration", 5)
            )

            if not scenes:
                raise RuntimeError("Không thể tạo kịch bản từ Story Engine.")

            # 3. Tạo Giọng đọc TTS & Subtitles
            total_scenes = len(scenes)
            safe_log(f"Dang tao TTS cho {total_scenes} canh...")
            scene_audio_files = []
            scene_srt_files = []

            for idx, sc in enumerate(scenes, start=1):
                a_path = str(job_dir / f"voice_sc_{idx}.mp3")
                s_path = str(job_dir / f"sub_sc_{idx}.srt")
                res = await tts_engine.generate_speech(
                    text=sc["text"],
                    output_audio_path=a_path,
                    output_srt_path=s_path,
                    voice=config.get("voice", "vi-VN-HoaiMyNeural"),
                    rate=config.get("rate", "+0%"),
                    pitch=config.get("pitch", "+0Hz")
                )
                scene_audio_files.append(a_path)
                scene_srt_files.append((s_path, res["duration"], sc["text"]))

            # 4. Tạo Hình ảnh AI
            safe_log(f"Dang tao {total_scenes} hinh anh AI...")
            scene_images = []
            for idx, sc in enumerate(scenes, start=1):
                img_path = str(job_dir / f"img_sc_{idx}.jpg")
                await visual_engine.generate_image(
                    prompt=sc["image_prompt"],
                    output_image_path=img_path,
                    style_key=config.get("genre", "dark_mystery"),
                    aspect_ratio=config.get("aspect_ratio", "16:9")
                )
                scene_images.append(img_path)

            # 5. Ken Burns & Render Video 1080p
            safe_log("Dang render clips Ken Burns va noi video...")
            scene_video_clips = []
            for idx, (img_p, (_, sc_dur, _)) in enumerate(zip(scene_images, scene_srt_files), start=1):
                clip_path = str(job_dir / f"clip_sc_{idx}.mp4")
                visual_engine.create_ken_burns_video(
                    image_path=img_p,
                    output_video_path=clip_path,
                    duration=sc_dur,
                    aspect_ratio=config.get("aspect_ratio", "16:9")
                )
                scene_video_clips.append(clip_path)

            base_video_path = str(job_dir / "base_video.mp4")
            render_engine.concat_scene_videos(scene_video_clips, base_video_path)

            # 6. Hòa âm âm thanh & Phụ đề
            full_voice_path = str(job_dir / "full_voice.mp3")
            audio_engine.concat_audio_files(scene_audio_files, full_voice_path)

            bgm_file = config.get("bgm_name")
            bgm_path = str(BGM_DIR / bgm_file) if bgm_file else None
            mixed_audio_path = str(job_dir / "mixed_audio.mp3")
            audio_engine.mix_voice_and_bgm(
                voice_path=full_voice_path,
                output_path=mixed_audio_path,
                bgm_path=bgm_path,
                bgm_volume=config.get("bgm_volume", 0.15)
            )

            from backend.app import _combine_srt_files
            final_full_srt = str(job_dir / "full_subtitles.srt")
            _combine_srt_files(scene_srt_files, final_full_srt)

            timestamp = int(time.time())
            clean_title_fn = "".join(c for c in topic if c.isalnum() or c in (" ", "_", "-")).rstrip().replace(" ", "_")[:40]
            final_video_filename = f"video_{clean_title_fn}_{timestamp}.mp4"
            final_video_output = str(OUTPUT_DIR / final_video_filename)

            render_engine.composite_final_video(
                base_video_path=base_video_path,
                audio_path=mixed_audio_path,
                output_path=final_video_output,
                srt_subtitles_path=final_full_srt,
                enable_waveform=config.get("enable_waveform", True),
                aspect_ratio=config.get("aspect_ratio", "16:9")
            )

            history_record["video_url"] = f"/output/{final_video_filename}"

            # 7. Tạo Thumbnail AI
            thumb_filename = f"thumb_{clean_title_fn}_{timestamp}.jpg"
            final_thumb_output = str(OUTPUT_DIR / thumb_filename)
            await visual_engine.generate_ai_thumbnail(
                title=topic,
                output_image_path=final_thumb_output,
                genre=config.get("genre", "dark_mystery"),
                topic=topic,
                style_key=config.get("genre", "dark_mystery"),
                aspect_ratio=config.get("aspect_ratio", "16:9")
            )
            history_record["thumbnail_url"] = f"/output/{thumb_filename}"

            # 8. Soạn Mô tả YouTube SEO
            desc_data = await story_engine.generate_video_description(
                title=topic,
                genre=config.get("genre", "dark_mystery"),
                topic=topic,
                scenes=scenes
            )
            full_description = desc_data.get("full_formatted_description", f"Truyện Audio: {topic}")
            tags = desc_data.get("seo_tags", ["TruyenAudio", "AudioStory"])

            # 9. Tự động Upload lên YouTube nếu được bật
            if config.get("auto_upload_youtube", False):
                safe_log("Dang tu dong upload len Kenh YouTube...")
                try:
                    yt_res = await youtube_engine.upload_video_to_youtube(
                        video_path=final_video_output,
                        title=topic,
                        description=full_description,
                        tags=tags,
                        privacy_status=config.get("privacy_status", "unlisted"),
                        thumbnail_path=final_thumb_output
                    )
                    history_record["youtube_url"] = yt_res.get("youtube_url", "")
                    history_record["youtube_status"] = "uploaded"
                    safe_log(f"Upload thanh cong: {history_record['youtube_url']}")
                except Exception as e:
                    history_record["youtube_status"] = "failed"
                    history_record["error"] = f"Lỗi upload YouTube: {str(e)}"
                    safe_log(f"Loi upload YouTube: {e}")

            history_record["status"] = "completed"

        except Exception as e:
            history_record["status"] = "error"
            history_record["error"] = str(e)
            safe_log(f"Loi quy trinh Auto-Pilot: {e}")
        finally:
            self.current_running_job = None
            self.append_history(history_record)

        return history_record

auto_scheduler = AutoScheduler()
