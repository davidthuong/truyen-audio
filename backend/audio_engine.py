import os
import subprocess
from pathlib import Path
from typing import List, Optional
from backend.config import BGM_DIR, TEMP_DIR

class AudioEngine:
    def __init__(self):
        self._ensure_sample_bgm()

    def _ensure_sample_bgm(self):
        """Tạo các file BGM mẫu không bản quyền bằng FFmpeg Synth nếu thư mục BGM rỗng"""
        ambient_file = BGM_DIR / "ambient_mystery.mp3"
        lofi_file = BGM_DIR / "lofi_peaceful.mp3"

        if not ambient_file.exists():
            # Tạo 1 đoạn nhạc nền ambient bí ẩn dạng drone âm trầm êm dịu 60s
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "anoisesrc=c=pink:r=44100:a=0.03,lowpass=f=300,volume=0.4",
                "-t", "60",
                "-c:a", "libmp3lame",
                "-b:a", "128k",
                str(ambient_file)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not lofi_file.exists():
            # Tạo 1 đoạn nhạc nền êm dịu phong cách lofi
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "anoisesrc=c=brown:r=44100:a=0.02,lowpass=f=400,volume=0.3",
                "-t", "60",
                "-c:a", "libmp3lame",
                "-b:a", "128k",
                str(lofi_file)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def concat_audio_files(self, audio_paths: List[str], output_path: str) -> str:
        """Nối danh sách các file audio thành 1 file duy nhất bằng FFmpeg"""
        concat_list_file = TEMP_DIR / f"concat_{os.getpid()}_{hash(output_path)%10000}.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for p in audio_paths:
                # Escape path cho ffmpeg concat demuxer
                clean_p = Path(p).resolve().as_posix().replace("'", "'\\''")
                f.write(f"file '{clean_p}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if concat_list_file.exists():
            concat_list_file.unlink()
        return output_path

    def mix_voice_and_bgm(
        self,
        voice_path: str,
        output_path: str,
        bgm_path: Optional[str] = None,
        bgm_volume: float = 0.15,
        total_duration: Optional[float] = None
    ) -> str:
        """
        Trộn giọng đọc (Voice) với Nhạc nền (BGM), tự động lặp BGM và làm mờ dần (Fade-out) ở cuối
        """
        if not bgm_path or not Path(bgm_path).exists():
            # Nếu không có BGM, chỉ cần copy/convert voice sang output
            cmd = [
                "ffmpeg", "-y",
                "-i", voice_path,
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                output_path
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return output_path

        # Trộn Voice + BGM lặp lại và fade out ở 3 giây cuối
        filter_complex = (
            f"[1:a]aloop=loop=-1:size=2e+09,volume={bgm_volume}[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", voice_path,
            "-i", bgm_path,
            "-filter_complex", filter_complex,
            "-map", "[aout]",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            output_path
        ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output_path

# Instance singleton
audio_engine = AudioEngine()
