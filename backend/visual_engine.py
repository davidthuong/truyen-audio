import os
import re
import time
import random
import base64
import asyncio
import subprocess
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from backend.config import VISUAL_STYLES, ASPECT_RATIOS, load_settings

class VisualEngine:
    def __init__(self):
        pass

    def _sanitize_and_optimize_prompt(self, raw_prompt: str, style_key: str) -> str:
        """
        Làm sạch, tối ưu hóa và khử các từ nhạy cảm dễ bị Proxy/OpenAI Safety Filter chặn:
        - Khử các từ nhạy cảm (trẻ em bị bỏ rơi, bạo lực, máu me, tai nạn) -> chuyển sang mô tả nghệ thuật điện ảnh an toàn.
        - Giới hạn độ dài chuẩn ~250-300 ký tự để API Proxy phản hồi nhanh nhất (dưới 15-20s).
        """
        sensitive_replacements = {
            r"\b(abandoned\s+child|abandoned\s+baby|left\s+alone\s+child|orphan\s+baby)\b": "young boy in elegant warm coat",
            r"\b(crying\s+baby|crying\s+child|toddler\s+in\s+danger)\b": "young child looking curiously",
            r"\b(dead\s+body|corpse|killed|murder|murdered|assassination)\b": "mysterious shadowy silhouette lying down",
            r"\b(blood|bloody|bleeding|wound|injured)\b": "dramatic crimson red backlight reflection",
            r"\b(weapon|gun|pistol|rifle|shooting|stab|stabbing)\b": "dramatic confrontation gesture",
            r"\b(torture|abuse|violent|violence|assault)\b": "intense psychological confrontation",
            r"\b(nude|naked|erotic|bikini|sexy)\b": "elegant luxury evening dress"
        }

        p = raw_prompt.strip()
        for pattern, replacement in sensitive_replacements.items():
            p = re.sub(pattern, replacement, p, flags=re.IGNORECASE)

        # Lấy style suffix
        style = VISUAL_STYLES.get(style_key, VISUAL_STYLES.get("dark_mystery", {}))
        suffix = style.get("prompt_suffix", "")

        # Ghép prompt và rút gọn hợp lý
        full = f"{p}, {suffix}".strip()
        parts = [part.strip() for part in full.split(",") if part.strip()]
        unique_parts = []
        seen = set()
        for pt in parts:
            low = pt.lower()
            if low not in seen:
                seen.add(low)
                unique_parts.append(pt)

        optimized = ", ".join(unique_parts)
        if len(optimized) > 300:
            optimized = optimized[:300].rsplit(",", 1)[0]

        return optimized

    async def generate_image(
        self,
        prompt: str,
        output_image_path: str,
        style_key: str = "dark_mystery",
        aspect_ratio: str = "16:9",
        seed: Optional[int] = None
    ) -> str:
        """
        Tạo ảnh AI theo prompt và phong cách visual
        Hỗ trợ: Custom OpenAI/DALL-E API endpoint hoặc Pollinations AI (Flux)
        """
        full_prompt = self._sanitize_and_optimize_prompt(prompt, style_key)

        settings = load_settings()
        api_key = settings.get("api_key", "").strip()
        base_url = settings.get("base_url", "https://api.openai.com/v1").strip().rstrip("/")
        image_model = settings.get("image_model", "dall-e-3").strip()
        image_provider = settings.get("image_provider", "pollinations")

        # 1. Thử gọi Custom OpenAI / Proxy API nếu được cấu hình
        if image_provider == "openai_dalle" and api_key:
            try:
                success = await self._generate_image_openai_dalle(
                    prompt=full_prompt,
                    output_path=output_image_path,
                    aspect_ratio=aspect_ratio,
                    base_url=base_url,
                    api_key=api_key,
                    model=image_model
                )
                if success:
                    return output_image_path
            except Exception as e:
                err_msg = str(e) or type(e).__name__
                print(f"Error calling Proxy Image API: {err_msg}. Fallback to Pollinations Flux...", flush=True)

        # 2. Tạo ảnh bằng Pollinations AI (Flux / SDXL - Fallback dự phòng)
        try:
            success = await self._generate_image_pollinations(
                prompt=full_prompt,
                output_path=output_image_path,
                aspect_ratio=aspect_ratio,
                seed=seed
            )
            if success:
                return output_image_path
        except Exception as e:
            err_msg = str(e) or type(e).__name__
            print(f"Error loading Pollinations image: {err_msg}. Generating gradient fallback...")

        # 3. Fallback tạo ảnh gradient chất lượng cao nếu offline
        dims = ASPECT_RATIOS.get(aspect_ratio, ASPECT_RATIOS["16:9"])
        self._generate_fallback_image(prompt, output_image_path, dims["width"], dims["height"], style_key)
        return output_image_path

    def _ensure_valid_jpeg(self, image_path: str, max_size: int = 1920, target_size: Optional[tuple] = (1280, 720)):
        """Đảm bảo ảnh là file JPEG chuẩn RGB, kích thước chuẩn YouTube và tối ưu dung lượng < 1.5MB"""
        try:
            if not os.path.exists(image_path):
                return
            with Image.open(image_path) as img:
                img = img.convert("RGB")
                if target_size:
                    img = img.resize(target_size, Image.Resampling.LANCZOS)
                elif max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                img.save(image_path, "JPEG", quality=88, optimize=True)
        except Exception as e:
            print(f"Lỗi chuẩn hóa ảnh JPEG ({image_path}): {e}")

    async def generate_ai_thumbnail(
        self,
        title: str,
        output_image_path: str,
        genre: str = "dark_mystery",
        topic: str = "",
        custom_prompt: Optional[str] = None,
        style_key: str = "dark_mystery",
        aspect_ratio: str = "16:9"
    ) -> str:
        """
        Tạo Thumbnail YouTube AI đẳng cấp chuẩn Cinematic 8K với chữ 3D nghệ thuật tích hợp trực tiếp
        """
        clean_title = title.strip()
        
        if custom_prompt and custom_prompt.strip():
            thumb_prompt = custom_prompt.strip()
        else:
            # Tự động kiến tạo Cinematic Prompt kích thích click (High CTR YouTube Style)
            style_info = VISUAL_STYLES.get(style_key, VISUAL_STYLES.get("dark_mystery", {}))
            genre_name = style_info.get("name", "Truyện Kịch Tính")
            
            thumb_prompt = (
                f"Cinematic ultra-realistic YouTube thumbnail, 16:9 widescreen, 8k resolution movie poster quality. "
                f"Dramatic story scene representing: '{clean_title}'. {topic if topic else ''}. "
                f"Powerful emotional focal point with intense character expression, dominant central figure, high-stakes conflict, "
                f"volumetric rim lighting, cinematic shadows, blockbuster movie aesthetic, hyper-detailed. "
                f"Integrated into the bottom area, prominent bold 3D metallic golden and fiery red typography in Vietnamese reading: '{clean_title}'."
            )

        print(f"Generating AI Thumbnail with prompt: {thumb_prompt[:120].encode('ascii', 'ignore').decode()}...")

        settings = load_settings()
        api_key = settings.get("api_key", "").strip()
        base_url = settings.get("base_url", "https://api.openai.com/v1").strip().rstrip("/")
        image_model = settings.get("image_model", "dall-e-3").strip()
        image_provider = settings.get("image_provider", "pollinations")

        # Thử tạo qua OpenAI DALL-E / Custom Proxy
        if image_provider == "openai_dalle" and api_key:
            try:
                success = await self._generate_image_openai_dalle(
                    prompt=thumb_prompt,
                    output_path=output_image_path,
                    aspect_ratio=aspect_ratio,
                    base_url=base_url,
                    api_key=api_key,
                    model=image_model
                )
                if success:
                    self._ensure_valid_jpeg(output_image_path)
                    return output_image_path
            except Exception as e:
                err_msg = str(e) or type(e).__name__
                print(f"Error calling Proxy Image API for Thumbnail: {err_msg}. Fallback to Pollinations...")

        # Thử tạo qua Pollinations Flux
        try:
            success = await self._generate_image_pollinations(
                prompt=thumb_prompt,
                output_path=output_image_path,
                aspect_ratio=aspect_ratio
            )
            if success:
                self._ensure_valid_jpeg(output_image_path)
                return output_image_path
        except Exception as e:
            err_msg = str(e) or type(e).__name__
            print(f"Error calling Pollinations for Thumbnail: {err_msg}. Fallback to PIL...")

        # Fallback dùng render_engine PIL
        from backend.render_engine import render_engine
        temp_bg = output_image_path + ".fallback.jpg"
        dims = ASPECT_RATIOS.get(aspect_ratio, ASPECT_RATIOS["16:9"])
        self._generate_fallback_image(clean_title, temp_bg, dims["width"], dims["height"], style_key)
        render_engine.generate_youtube_thumbnail(temp_bg, output_image_path, clean_title, "TRUYỆN AUDIO")
        if os.path.exists(temp_bg):
            try: os.remove(temp_bg)
            except Exception: pass
        self._ensure_valid_jpeg(output_image_path)
        return output_image_path

    async def _generate_image_openai_dalle(
        self,
        prompt: str,
        output_path: str,
        aspect_ratio: str,
        base_url: str,
        api_key: str,
        model: str,
        max_retries: int = 3
    ) -> bool:
        """Tạo ảnh qua endpoint /v1/images/generations với tương thích đa kích thước cho proxy và cơ chế retry tự động"""
        # Hầu hết các proxy model (gpt-image-2, custom SD/Midjourney) chỉ chấp nhận 1024x1024
        if "dall-e-3" in model:
            size = "1792x1024" if aspect_ratio == "16:9" else ("1024x1792" if aspect_ratio == "9:16" else "1024x1024")
        else:
            size = "1024x1024"

        headers = {
            "Authorization": f"Bearer {api_key}" if api_key else "Bearer sk-none",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size
        }

        timeout = aiohttp.ClientTimeout(total=45, connect=10)

        for attempt in range(1, max_retries + 1):
            try:
                start_t = time.time()
                print(f"[Proxy Image] Dang goi API Proxy ({model}) - Lan thu {attempt}/{max_retries}...", flush=True)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(f"{base_url}/images/generations", headers=headers, json=payload) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if "data" in data and len(data["data"]) > 0:
                                item = data["data"][0]
                                if "b64_json" in item and item["b64_json"]:
                                    img_bytes = base64.b64decode(item["b64_json"])
                                    with open(output_path, "wb") as f:
                                        f.write(img_bytes)
                                    dur = time.time() - start_t
                                    print(f"[Proxy Image] Tao anh thanh cong qua Proxy ({model}) trong {dur:.1f}s!", flush=True)
                                    return True
                                elif "url" in item and item["url"]:
                                    async with session.get(item["url"], timeout=aiohttp.ClientTimeout(total=30)) as img_resp:
                                        if img_resp.status == 200:
                                            img_data = await img_resp.read()
                                            if len(img_data) > 5000:
                                                with open(output_path, "wb") as f:
                                                    f.write(img_data)
                                                dur = time.time() - start_t
                                                print(f"[Proxy Image] Tai & luu anh thanh cong ({model}) trong {dur:.1f}s!", flush=True)
                                                return True
                        else:
                            err_body = await resp.text()
                            print(f"[Proxy Image] API error ({model}) Status {resp.status}: {err_body[:150]}", flush=True)
            except Exception as e:
                err_msg = str(e) or type(e).__name__
                print(f"[Proxy Image] Lan {attempt} that bai: {err_msg}", flush=True)
            
            if attempt < max_retries:
                wait_sec = attempt * 2
                print(f"[Proxy Image] Cho {wait_sec}s truoc khi thu lai...", flush=True)
                await asyncio.sleep(wait_sec)

        return False

    async def _generate_image_pollinations(
        self,
        prompt: str,
        output_path: str,
        aspect_ratio: str,
        seed: Optional[int] = None
    ) -> bool:
        """Tạo ảnh qua Pollinations AI với đa mô hình (Flux -> Turbo -> Standard) đảm bảo 100% thành công"""
        if seed is None:
            seed = random.randint(1000, 999999)

        if aspect_ratio == "16:9":
            gen_w, gen_h = 1280, 720
        else:
            gen_w, gen_h = 720, 1280

        # Rút gọn prompt nếu quá dài để tránh lỗi URL
        clean_prompt = prompt.strip()
        if len(clean_prompt) > 300:
            clean_prompt = clean_prompt[:300].rsplit(",", 1)[0]

        encoded_prompt = urllib.parse.quote(clean_prompt)

        # Thử lần lượt: turbo (siêu tốc 2s) -> flux -> default
        models_to_try = ["turbo", "flux", "default"]

        for mod in models_to_try:
            try:
                if mod == "default":
                    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={gen_w}&height={gen_h}&seed={seed}&nologo=true"
                else:
                    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={gen_w}&height={gen_h}&seed={seed}&nologo=true&model={mod}"

                timeout = aiohttp.ClientTimeout(total=20, connect=8)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            image_data = await resp.read()
                            if len(image_data) > 5000: # Đảm bảo file ảnh hợp lệ không rỗng
                                with open(output_path, "wb") as f:
                                    f.write(image_data)
                                return True
            except Exception as e:
                print(f"Pollinations model '{mod}' retry next. Error: {e}")
                continue

        return False

    def _generate_fallback_image(self, prompt: str, output_path: str, width: int, height: int, style_key: str):
        # Nền gradient điện ảnh nghệ thuật
        img = Image.new("RGB", (width, height), color="#0b0f19")
        draw = ImageDraw.Draw(img)
        for y in range(height):
            r = int(11 + (y / height) * 25)
            g = int(15 + (y / height) * 35)
            b = int(25 + (y / height) * 55)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        img.save(output_path, "JPEG", quality=95)

    def create_ken_burns_video(
        self,
        image_path: str,
        output_video_path: str,
        duration: float,
        aspect_ratio: str = "16:9",
        motion_type: Optional[str] = None
    ) -> str:
        """Áp dụng hiệu ứng chuyển động Ken Burns tối ưu hóa đa luồng và tốc độ render nhanh"""
        dims = ASPECT_RATIOS.get(aspect_ratio, ASPECT_RATIOS["16:9"])
        width = dims["width"]
        height = dims["height"]
        duration = max(1.0, float(duration))
        fps = 25  # 25fps mượt mà và giảm tải đáng kể cho CPU
        total_frames = int(duration * fps) + 2

        if not Path(image_path).exists() or Path(image_path).stat().st_size < 500:
            self._generate_fallback_image("Scenery", image_path, width, height, "dark_mystery")

        if not motion_type:
            motion_type = random.choice(["zoom_in", "zoom_out", "pan_left", "pan_right"])

        if motion_type == "zoom_in":
            vf = (
                f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
                f"zoompan=z='min(zoom+0.0015,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps},"
                f"format=yuv420p"
            )
        elif motion_type == "zoom_out":
            vf = (
                f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
                f"zoompan=z='if(lte(zoom,1.0),1.2,max(1.001,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps},"
                f"format=yuv420p"
            )
        elif motion_type == "pan_left":
            vf = (
                f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
                f"zoompan=z=1.12:x='if(lte(on,-1),(iw-iw/zoom)/2,x-0.4)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps},"
                f"format=yuv420p"
            )
        else:
            vf = (
                f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
                f"zoompan=z=1.12:x='if(lte(on,-1),0,x+0.4)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps},"
                f"format=yuv420p"
            )

        cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-loop", "1",
            "-i", image_path,
            "-vf", vf,
            "-t", f"{duration:.3f}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            output_video_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            fallback_cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                "-loop", "1",
                "-i", image_path,
                "-t", f"{duration:.3f}",
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},format=yuv420p",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "ultrafast",
                output_video_path
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        return output_video_path

# Instance singleton
visual_engine = VisualEngine()
