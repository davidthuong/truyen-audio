import os
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from backend.config import BASE_DIR, TEMP_DIR, OUTPUT_DIR, ASPECT_RATIOS

class RenderEngine:
    def __init__(self):
        pass

    def concat_scene_videos(self, video_clips: List[str], output_video_path: str) -> str:
        """Ghép các video clip từng scene lại với nhau an toàn tuyệt đối"""
        valid_clips = [v for v in video_clips if Path(v).exists() and Path(v).stat().st_size > 1000]
        if not valid_clips:
            raise RuntimeError("Không có clip video nào được render hợp lệ để ghép nối.")

        list_file = TEMP_DIR / f"video_list_{os.getpid()}_{hash(output_video_path)%10000}.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for v in valid_clips:
                clean_path = Path(v).resolve().as_posix()
                f.write(f"file '{clean_path}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            output_video_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if list_file.exists():
            try:
                list_file.unlink()
            except Exception:
                pass

        if res.returncode != 0:
            print(f"Concat list demuxer error: {res.stderr[:200]}. Trying filter concat fallback...")
            # Fallback dùng filter_complex concat
            inputs = []
            filter_parts = []
            for i, v in enumerate(valid_clips):
                inputs.extend(["-i", v])
                filter_parts.append(f"[{i}:v]")
            filter_str = f"{''.join(filter_parts)}concat=n={len(valid_clips)}:v=1:a=0[outv]"
            fallback_cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                *inputs,
                "-filter_complex", filter_str,
                "-map", "[outv]",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "ultrafast",
                output_video_path
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        return output_video_path

    def composite_final_video(
        self,
        base_video_path: str,
        audio_path: str,
        output_path: str,
        srt_subtitles_path: Optional[str] = None,
        title_text: Optional[str] = None,
        watermark_text: Optional[str] = None,
        enable_waveform: bool = True,
        aspect_ratio: str = "16:9"
    ) -> str:
        """
        Dựng video thành phẩm hoàn chỉnh với Âm thanh + Sóng âm + Phụ đề + Watermark/Title
        """
        dims = ASPECT_RATIOS.get(aspect_ratio, ASPECT_RATIOS["16:9"])
        width = dims["width"]
        height = dims["height"]

        filters = []
        current_v = "[0:v]"

        # 1. Hiệu ứng làm tối nhẹ góc (Vignette)
        filters.append(f"{current_v}vignette=PI/4[v_vignette]")
        current_v = "[v_vignette]"

        # 2. Hiệu ứng Sóng âm Audio Waveform
        if enable_waveform:
            wave_w = int(width * 0.7)
            wave_h = int(height * 0.12)
            wave_x = int((width - wave_w) / 2)
            wave_y = int(height * 0.78) if aspect_ratio == "16:9" else int(height * 0.75)

            filters.append(
                f"[1:a]showwaves=s={wave_w}x{wave_h}:mode=line:colors=0x38bdf8@0.75:scale=sqrt,format=yuva420p[wave_alpha];"
                f"{current_v}[wave_alpha]overlay={wave_x}:{wave_y}[v_wave]"
            )
            current_v = "[v_wave]"

        # 3. Phụ đề (Subtitles) - Dùng đường dẫn tương đối để tránh lỗi ký tự ổ đĩa trên Windows
        if srt_subtitles_path and Path(srt_subtitles_path).exists():
            rel_sub_path = os.path.relpath(Path(srt_subtitles_path).resolve(), os.getcwd()).replace("\\", "/")
            filters.append(f"{current_v}subtitles=filename='{rel_sub_path}'[v_sub]")
            current_v = "[v_sub]"

        filter_complex_str = ";".join(filters)

        cmd = [
            "ffmpeg", "-y",
            "-i", base_video_path,
            "-i", audio_path,
            "-filter_complex", filter_complex_str,
            "-map", current_v,
            "-map", "1:a",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"FFmpeg composite failed: {res.stderr}")
            # Fallback giản lược nếu có lỗi filter
            fallback_cmd = [
                "ffmpeg", "-y",
                "-i", base_video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                output_path
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        return output_path

    def generate_youtube_thumbnail(
        self,
        base_image_path: str,
        output_thumb_path: str,
        title: str,
        subtitle: str = "TRUYỆN AUDIO ĐẶC SẮC"
    ) -> str:
        """Tự động tạo Thumbnail chuẩn YouTube 1280x720 bắt mắt hỗ trợ tiếng Việt có dấu"""
        try:
            img = Image.open(base_image_path).convert("RGB")
            img = img.resize((1280, 720), Image.Resampling.LANCZOS)
            
            # Thêm lớp phủ tối ở nửa dưới
            overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
            draw_ov = ImageDraw.Draw(overlay)
            
            for y in range(360, 720):
                alpha = int(((y - 360) / 360) * 210)
                draw_ov.line([(0, y), (1280, y)], fill=(0, 0, 0, alpha))
                
            img.paste(overlay, (0, 0), overlay)
            draw = ImageDraw.Draw(img)

            # Tải TrueType font hỗ trợ UTF-8 tiếng Việt (Hỗ trợ đa nền tảng Windows, Linux VPS/Server, macOS)
            font_title = None
            font_sub = None
            font_candidates = [
                # Windows fonts
                "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/tahoma.ttf", "C:/Windows/Fonts/segoeui.ttf",
                # Linux fonts (Ubuntu / Debian / CentOS / Docker)
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
                "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
                "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
                # macOS fonts
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/Library/Fonts/Arial.ttf"
            ]
            for fp in font_candidates:
                if os.path.exists(fp):
                    try:
                        font_title = ImageFont.truetype(fp, 42)
                        font_sub = ImageFont.truetype(fp, 24)
                        break
                    except Exception:
                        pass
            if not font_title:
                try:
                    font_title = ImageFont.load_default()
                    font_sub = ImageFont.load_default()
                except Exception:
                    pass

            # Badge tag
            sub_text = subtitle.upper()
            bbox_sub = draw.textbbox((0, 0), sub_text, font=font_sub) if hasattr(draw, "textbbox") else (0, 0, len(sub_text)*14, 28)
            sub_w = bbox_sub[2] - bbox_sub[0]
            badge_x1 = 60
            badge_y1 = 460
            badge_x2 = badge_x1 + sub_w + 32
            badge_y2 = badge_y1 + 42
            draw.rectangle([badge_x1, badge_y1, badge_x2, badge_y2], fill="#ef4444")
            draw.text((badge_x1 + 16, badge_y1 + 8), sub_text, fill="#ffffff", font=font_sub)

            # Tự động xuống dòng cho tiêu đề dài (Word wrap)
            import textwrap
            max_chars_per_line = 32 if len(title) > 60 else 36
            wrapped_lines = textwrap.wrap(title.strip(), width=max_chars_per_line)
            if len(wrapped_lines) > 3:
                wrapped_lines = wrapped_lines[:3]
                wrapped_lines[-1] = wrapped_lines[-1].rstrip("., ") + "..."

            # Giảm kích thước font nếu tiêu đề có nhiều dòng
            if len(wrapped_lines) >= 3:
                font_title_dyn = ImageFont.truetype(font_title.path, 34) if hasattr(font_title, 'path') else font_title
                line_spacing = 44
                title_y = 515
            elif len(wrapped_lines) == 2:
                font_title_dyn = ImageFont.truetype(font_title.path, 38) if hasattr(font_title, 'path') else font_title
                line_spacing = 48
                title_y = 525
            else:
                font_title_dyn = font_title
                line_spacing = 52
                title_y = 545

            # Vẽ từng dòng tiêu đề có viền đen (shadow/stroke) chống chìm nền
            for i, line in enumerate(wrapped_lines):
                cur_y = title_y + (i * line_spacing)
                # Viền đen dày để nổi bật trên mọi hình nền
                for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (0, 2), (0, -2), (2, 0), (-2, 0), (0, 3)]:
                    draw.text((60 + dx, cur_y + dy), line, fill="#000000", font=font_title_dyn)
                # Màu chữ vàng sáng bắt mắt
                draw.text((60, cur_y), line, fill="#facc15", font=font_title_dyn)
            
            img.save(output_thumb_path, "JPEG", quality=95)
            return output_thumb_path
        except Exception as e:
            print(f"Thumbnail generation warning: {e}, using raw image fallback.")
            try:
                shutil.copyfile(base_image_path, output_thumb_path)
            except Exception:
                pass
            return output_thumb_path

# Instance singleton
render_engine = RenderEngine()
