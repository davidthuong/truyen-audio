import asyncio
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import edge_tts
import mutagen
from mutagen.mp3 import MP3

import aiohttp
import json
import time
from backend.config import load_settings

def format_timestamp_srt(seconds: float) -> str:
    """Định dạng thời gian sang chuẩn SRT (HH:MM:SS,mmm)"""
    millis = int(round((seconds - int(seconds)) * 1000))
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def format_timestamp_ass(seconds: float) -> str:
    """Định dạng thời gian sang chuẩn ASS (H:MM:SS.cc)"""
    centis = int(round((seconds - int(seconds)) * 100))
    if centis == 100:
        centis = 99
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:d}:{mins:02d}:{secs:02d}.{centis:02d}"

class TTSEngine:
    def __init__(self):
        pass

    async def get_vivibe_voices_detail(self, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Lấy danh sách các giọng đọc từ tài khoản ViVibe (LucyAI) kèm thông báo chi tiết"""
        settings = load_settings()
        key = (api_key or settings.get("vivibe_api_key", "")).strip()
        if key.lower().startswith("bearer "):
            key = key[7:].strip()
        
        if not key:
            return {"status": "error", "message": "Chưa nhập ViVibe API Key.", "voices": []}

        url = "https://api.lucylab.io/json-rpc"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        payload = {
            "method": "getUserVoices",
            "input": {
                "limit": 50,
                "page": 1
            }
        }

        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    resp_text = await resp.text()
                    if resp.status == 200:
                        try:
                            data = json.loads(resp_text)
                        except Exception:
                            return {"status": "error", "message": f"Phản hồi không hợp lệ: {resp_text[:100]}", "voices": []}

                        if "error" in data:
                            err_msg = data["error"].get("message") if isinstance(data["error"], dict) else str(data["error"])
                            return {"status": "error", "message": f"ViVibe báo lỗi: {err_msg}", "voices": []}

                        result = data.get("result", {})
                        items = result.get("items", [])
                        voices = [
                            {
                                "id": f"vivibe:{item.get('id')}",
                                "raw_id": item.get("id"),
                                "name": f"[ViVibe AI] {item.get('name', 'Voice')}",
                                "isActive": item.get("isActive", True)
                            }
                            for item in items if item.get("id")
                        ]
                        return {
                            "status": "ok",
                            "voices": voices,
                            "total": len(voices),
                            "message": "Thành công" if voices else "Tài khoản của bạn chưa có giọng tự tạo/clone trên ViVibe. Bạn có thể dán trực tiếp Voice ID vào ô nhập bên dưới!"
                        }
                    else:
                        return {"status": "error", "message": f"ViVibe HTTP {resp.status}: {resp_text[:150]}", "voices": []}
        except Exception as e:
            return {"status": "error", "message": f"Lỗi kết nối ViVibe: {str(e)}", "voices": []}

    async def get_vivibe_voices(self, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lấy danh sách các giọng đọc từ tài khoản ViVibe (LucyAI)"""
        res = await self.get_vivibe_voices_detail(api_key=api_key)
        return res.get("voices", [])

    async def generate_speech(
        self,
        text: str,
        output_audio_path: str,
        output_srt_path: Optional[str] = None,
        output_ass_path: Optional[str] = None,
        voice: str = "vi-VN-HoaiMyNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> Dict[str, Any]:
        """
        Chuyển text thành audio mp3/wav và phụ đề srt
        Hỗ trợ: ViVibe (LucyAI) và Edge-TTS (Fallback)
        """
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Nội dung text trống.")

        settings = load_settings()
        tts_provider = settings.get("tts_provider", "edge_tts")
        vivibe_api_key = settings.get("vivibe_api_key", "").strip()

        # Kiểm tra nếu người dùng chọn giọng ViVibe hoặc cấu hình provider là vivibe
        is_vivibe = (
            voice.startswith("vivibe:") or 
            (tts_provider == "vivibe" and vivibe_api_key and not voice.startswith("vi-VN-") and not voice.startswith("en-US-"))
        )

        if is_vivibe and vivibe_api_key:
            target_voice_id = voice.replace("vivibe:", "").strip() or settings.get("vivibe_voice_id", "").replace("vivibe:", "").strip()
            if target_voice_id:
                try:
                    res = await self._generate_speech_vivibe(
                        text=clean_text,
                        output_audio_path=output_audio_path,
                        output_srt_path=output_srt_path,
                        output_ass_path=output_ass_path,
                        voice_id=target_voice_id,
                        api_key=vivibe_api_key,
                        rate=rate
                    )
                    return res
                except Exception as e:
                    print(f"[ViVibe TTS] Lỗi khi tạo giọng qua ViVibe ({e}). Đang tự động chuyển sang Edge-TTS dự phòng...")

        # Mặc định / Fallback dùng Edge-TTS
        return await self._generate_speech_edge_tts(
            clean_text=clean_text,
            output_audio_path=output_audio_path,
            output_srt_path=output_srt_path,
            output_ass_path=output_ass_path,
            voice="vi-VN-HoaiMyNeural" if voice.startswith("vivibe:") else voice,
            rate=rate,
            pitch=pitch,
            volume=volume
        )

    async def _generate_speech_vivibe(
        self,
        text: str,
        output_audio_path: str,
        output_srt_path: Optional[str],
        output_ass_path: Optional[str],
        voice_id: str,
        api_key: str,
        rate: str = "+0%"
    ) -> Dict[str, Any]:
        """Tạo giọng đọc chuyên nghiệp từ ViVibe (LucyAI) JSON-RPC API"""
        url = "https://api.lucylab.io/json-rpc"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Chuyển đổi rate (+10%, -10%) sang speed float (0.9 - 1.1)
        speed = 1.0
        try:
            if rate.startswith("+") and rate.endswith("%"):
                pct = int(rate[1:-1])
                speed = round(1.0 + (pct / 100.0), 2)
            elif rate.startswith("-") and rate.endswith("%"):
                pct = int(rate[1:-1])
                speed = round(1.0 - (pct / 100.0), 2)
        except Exception:
            speed = 1.0

        # Bước 1: Khởi tạo TTS job (ttsLongText)
        payload = {
            "method": "ttsLongText",
            "input": {
                "text": text,
                "userVoiceId": voice_id,
                "speed": max(0.5, min(2.0, speed))
            }
        }

        print(f"[ViVibe TTS] Dang gui yeu cau doc ({len(text)} ky tu) - Voice ID: {voice_id}...")
        timeout = aiohttp.ClientTimeout(total=45, connect=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    err_txt = await resp.text()
                    raise RuntimeError(f"ViVibe API Error {resp.status}: {err_txt[:200]}")
                
                data = await resp.json()
                result = data.get("result", {})
                export_id = result.get("projectExportId")
                if not export_id:
                    raise RuntimeError(f"ViVibe không trả về projectExportId: {data}")

        # Bước 2: Polling lấy kết quả âm thanh qua getExportStatus (Tối đa 90 giây)
        poll_payload = {
            "method": "getExportStatus",
            "input": {
                "projectExportId": export_id
            }
        }

        max_wait_seconds = 90
        start_poll = time.time()
        audio_url = None
        srt_url = None

        async with aiohttp.ClientSession(timeout=timeout) as session:
            while time.time() - start_poll < max_wait_seconds:
                await asyncio.sleep(2.0)
                async with session.post(url, headers=headers, json=poll_payload) as resp:
                    if resp.status == 200:
                        status_data = await resp.json()
                        st_res = status_data.get("result", {})
                        state = st_res.get("state")
                        
                        if state == "completed":
                            audio_url = st_res.get("url")
                            srt_url = st_res.get("srtUrl")
                            break
                        elif state == "failed":
                            raise RuntimeError(f"ViVibe TTS render thất bại: {status_data}")
                    else:
                        print(f"[ViVibe TTS] Polling status HTTP {resp.status}...")

        if not audio_url:
            raise TimeoutError("ViVibe TTS xử lý quá 90 giây mà chưa hoàn thành.")

        # Bước 3: Tải file Audio về máy
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.get(audio_url) as a_resp:
                if a_resp.status == 200:
                    with open(output_audio_path, "wb") as f:
                        f.write(await a_resp.read())
                else:
                    raise RuntimeError(f"Không tải được audio từ ViVibe: HTTP {a_resp.status}")

            # Bước 4: Tải file SRT nếu có
            if srt_url and output_srt_path:
                try:
                    async with session.get(srt_url) as s_resp:
                        if s_resp.status == 200:
                            with open(output_srt_path, "wb") as f:
                                f.write(await s_resp.read())
                except Exception as e:
                    print(f"[ViVibe TTS] Lỗi tải SRT: {e}")

        # Đo độ dài file audio chính xác
        duration = self.get_audio_duration(output_audio_path)

        # Nếu không có srt từ API thì tạo srt 1 khối cơ bản
        if output_srt_path and (not os.path.exists(output_srt_path) or os.path.getsize(output_srt_path) == 0):
            with open(output_srt_path, "w", encoding="utf-8") as f:
                f.write(f"1\n00:00:00,000 --> {format_timestamp_srt(duration)}\n{text}\n")

        print(f"[ViVibe TTS] Xuat giong doc thanh cong: {duration:.1f}s!")
        return {
            "audio_path": output_audio_path,
            "duration": duration,
            "voice": f"vivibe:{voice_id}",
            "srt_path": output_srt_path,
            "ass_path": output_ass_path
        }

    async def _generate_speech_edge_tts(
        self,
        clean_text: str,
        output_audio_path: str,
        output_srt_path: Optional[str],
        output_ass_path: Optional[str],
        voice: str,
        rate: str,
        pitch: str,
        volume: str
    ) -> Dict[str, Any]:
        """Tạo giọng đọc qua Edge-TTS (Miễn phí)"""
        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                communicate = edge_tts.Communicate(
                    clean_text,
                    voice=voice,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )

                sub_maker = edge_tts.SubMaker()
                has_audio = False
                
                # Tạo audio và ghi nhận subtitles
                with open(output_audio_path, "wb") as file:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            file.write(chunk["data"])
                            has_audio = True
                        elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                            sub_maker.feed(chunk)

                if not has_audio or not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
                    raise RuntimeError("Không nhận được dữ liệu âm thanh từ Edge TTS.")

                # Đo độ dài file audio chính xác
                duration = self.get_audio_duration(output_audio_path)

                # Xuất SRT nếu được yêu cầu
                if output_srt_path:
                    try:
                        srt_content = sub_maker.get_srt()
                    except Exception:
                        srt_content = ""
                    
                    if not srt_content.strip():
                        srt_content = f"1\n00:00:00,000 --> {format_timestamp_srt(duration)}\n{clean_text}\n"
                    with open(output_srt_path, "w", encoding="utf-8") as f:
                        f.write(srt_content)

                # Xuất ASS nếu được yêu cầu
                if output_ass_path:
                    self._generate_styled_ass(clean_text, duration, output_ass_path, sub_maker)

                return {
                    "audio_path": output_audio_path,
                    "duration": duration,
                    "voice": voice,
                    "srt_path": output_srt_path,
                    "ass_path": output_ass_path
                }

            except Exception as e:
                last_error = e
                await asyncio.sleep(1.0 * attempt)

        raise last_error

    def get_audio_duration(self, audio_path: str) -> float:
        """Đo thời lượng file audio tính bằng giây"""
        try:
            audio = MP3(audio_path)
            return float(audio.info.length)
        except Exception:
            # Fallback nếu mutagen gặp vấn đề
            import subprocess
            cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", audio_path
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return float(res.stdout.strip())

    def _generate_styled_ass(self, full_text: str, duration: float, ass_path: str, sub_maker: edge_tts.SubMaker):
        """
        Tạo file phụ đề ASS với style nghệ thuật, font đẹp, bóng đổ chuyên nghiệp cho video YouTube
        """
        ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: StoryDefault,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,3,2,2,80,80,90,1
Style: StoryHighlight,Arial,52,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,3,3,2,80,80,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        raw_srt = sub_maker.get_srt()
        
        if raw_srt.strip():
            # Parse các block srt từ sub_maker để chuyển thành ASS
            blocks = raw_srt.strip().split("\n\n")
            for block in blocks:
                lines = block.strip().split("\n")
                if len(lines) >= 3:
                    time_line = lines[1]
                    sub_text = " ".join(lines[2:])
                    # Parse time: 00:00:01,234 --> 00:00:03,456
                    match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})", time_line)
                    if match:
                        start_str, end_str = match.groups()
                        # Đổi thành format ASS H:MM:SS.cc
                        start_ass = self._srt_time_to_ass(start_str)
                        end_ass = self._srt_time_to_ass(end_str)
                        events.append(f"Dialogue: 0,{start_ass},{end_ass},StoryDefault,,0,0,0,,{sub_text}")
        
        if not events:
            # Fallback nếu không có sub boundaries
            start_ass = "0:00:00.00"
            end_ass = format_timestamp_ass(duration)
            events.append(f"Dialogue: 0,{start_ass},{end_ass},StoryDefault,,0,0,0,,{full_text}")

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(events) + "\n")

    def _srt_time_to_ass(self, srt_time: str) -> str:
        # srt: 00:01:23,456 -> ass: 0:01:23.45
        time_part, millis = srt_time.split(",")
        hours, mins, secs = time_part.split(":")
        centis = int(millis) // 10
        return f"{int(hours)}:{mins}:{secs}.{centis:02d}"

# Instance singleton
tts_engine = TTSEngine()
