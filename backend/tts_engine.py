import asyncio
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import edge_tts
import mutagen
from mutagen.mp3 import MP3

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
        Chuyển text thành audio mp3 và phụ đề srt/ass có timestamp từ Edge TTS
        """
        # Làm sạch text
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Nội dung text trống.")

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
