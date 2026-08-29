import re
import json
import asyncio
import urllib.parse
import aiohttp
from typing import List, Dict, Any, Optional
from backend.config import VISUAL_STYLES, load_settings

class StoryEngine:
    def __init__(self):
        pass

    async def generate_story(
        self,
        genre: str = "dark_mystery",
        topic: str = "Ngôi nhà cổ giữa rừng thông lúc nửa đêm",
        target_minutes: int = 5,
        num_scenes: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Tạo kịch bản truyện theo thời lượng (5p, 15p, 30p, 45p) sử dụng Custom ChatGPT API hoặc AI Engine
        """
        settings = load_settings()
        api_key = settings.get("api_key", "").strip()
        base_url = settings.get("base_url", "https://api.openai.com/v1").strip().rstrip("/")
        model = settings.get("chat_model", "gpt-4o-mini").strip()

        # Tính toán số lượng scene ước lượng (trung bình 1 scene dài ~45-60s hoặc ~100-140 từ tiếng Việt)
        if num_scenes is None:
            # 5 phút = 5-6 scenes, 15 phút = 15-18 scenes, 30 phút = 30-35 scenes, 45 phút = 45-50 scenes
            num_scenes = max(3, int(target_minutes * 1.1))

        # Nếu có cấu hình Custom API Key (ChatGPT / OpenRouter / Groq / OneAPI...)
        if api_key:
            try:
                if target_minutes >= 15:
                    # Tạo truyện dài theo từng chương để giữ tính liền mạch và không bị cắt cụt
                    return await self._generate_long_story_openai(genre, topic, target_minutes, num_scenes, base_url, api_key, model)
                else:
                    return await self._generate_short_story_openai(genre, topic, num_scenes, base_url, api_key, model)
            except Exception as e:
                print(f"Lỗi khi gọi Custom ChatGPT API ({e}), đang chuyển sang AI dự phòng...")

        # Fallback qua Pollinations AI hoặc template
        return await self._generate_story_pollinations_or_fallback(genre, topic, num_scenes)

    async def _generate_short_story_openai(
        self,
        genre: str,
        topic: str,
        num_scenes: int,
        base_url: str,
        api_key: str,
        model: str
    ) -> List[Dict[str, Any]]:
        """Tạo truyện ngắn với Custom ChatGPT API"""
        system_prompt = (
            "Bạn là một nhà biên kịch truyện audio YouTube / Radio kịch bản chuyên nghiệp. "
            "Hãy viết nội dung kể chuyện cực kỳ lôi cuốn, giọng văn giàu cảm xúc, hồi hộp và sâu lắng. "
            "Định dạng kết quả trả về BẮT BUỘC là JSON Array thuần túy, không có text nào khác."
        )

        user_prompt = f"""Hãy viết một câu chuyện audio thuộc thể loại '{genre}', chủ đề: '{topic}'.
Chia câu chuyện thành đúng {num_scenes} phân cảnh (scenes).
Mỗi phân cảnh cần:
1. 'scene': số thứ tự (int)
2. 'text': Đoạn lời dẫn/kể chuyện bằng tiếng Việt truyền cảm, giàu hình tượng, nhịp điệu phù hợp đọc audio (khoảng 60-120 từ mỗi scene).
3. 'image_prompt': Một câu prompt mô tả chi tiết bối cảnh hình ảnh bằng tiếng Anh (không có text, không watermark) để tạo ảnh AI nghệ thuật.

Ví dụ định dạng trả về:
[
  {{"scene": 1, "text": "Lời dẫn cảnh 1...", "image_prompt": "cinematic moody lighting, deep ancient forest, mist..."}},
  ...
]
Chỉ trả về mảng JSON!"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.8
        }

        timeout = aiohttp.ClientTimeout(total=45, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{base_url}/chat/completions", headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    json_match = re.search(r"\[.*\]", content, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(0))
                else:
                    err_txt = await resp.text()
                    raise RuntimeError(f"OpenAI API Error {resp.status}: {err_txt[:200]}")

        raise RuntimeError("Không parse được JSON từ response ChatGPT.")

    async def _generate_long_story_openai(
        self,
        genre: str,
        topic: str,
        target_minutes: int,
        total_scenes: int,
        base_url: str,
        api_key: str,
        model: str
    ) -> List[Dict[str, Any]]:
        """
        Tạo kịch bản truyện dài (30-45 phút):
        Chia thành các Chương (Chapters), mỗi chương sinh các Scene chi tiết liên kết chặt chẽ.
        """
        num_chapters = max(3, target_minutes // 6)
        scenes_per_chapter = max(3, total_scenes // num_chapters)

        # Bước 1: Lập dàn ý các chương
        print(f"[Custom AI] Đang lập dàn ý {num_chapters} chương cho truyện {target_minutes} phút ({model})...")
        outline_prompt = f"""Bạn là một tiểu thuyết gia và biên kịch audio chuyên nghiệp.
Hãy lập dàn ý một câu chuyện dài {target_minutes} phút, thể loại '{genre}', chủ đề: '{topic}'.
Hãy chia câu chuyện thành đúng {num_chapters} chương (hồi) có cốt truyện hấp dẫn, kịch tính, nút thắt và cao trào.
Trả về JSON:
[
  {{"chapter": 1, "title": "Tên chương 1", "summary": "Tóm tắt diễn biến chương 1..."}},
  ...
]
Chỉ trả về JSON Array."""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        chapters_outline = []
        try:
            timeout_outline = aiohttp.ClientTimeout(total=45, connect=10)
            async with aiohttp.ClientSession(timeout=timeout_outline) as session:
                async with session.post(f"{base_url}/chat/completions", headers=headers, json={
                    "model": model,
                    "messages": [{"role": "user", "content": outline_prompt}],
                    "temperature": 0.7
                }) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        m = re.search(r"\[.*\]", content, re.DOTALL)
                        if m:
                            chapters_outline = json.loads(m.group(0))
                            print(f"[Custom AI] Đã lập xong dàn ý {len(chapters_outline)} chương! Bắt đầu viết chi tiết...")
                    else:
                        err_body = await resp.text()
                        print(f"[Custom AI] Lỗi lập dàn ý ({resp.status}): {err_body[:120]}")
        except Exception as e:
            print(f"[Custom AI] Lỗi kết nối khi lập dàn ý ({e})")

        if not chapters_outline:
            # Fallback tạo dàn ý cơ bản
            print("[Custom AI] Sử dụng dàn ý mặc định để tiếp tục viết...")
            chapters_outline = [
                {"chapter": i+1, "title": f"Hồi {i+1}", "summary": f"Diễn biến phần {i+1} của câu chuyện {topic}"}
                for i in range(num_chapters)
            ]

        # Bước 2: Sinh chi tiết các chương (Dùng Semaphore 2 luồng để không làm nghẽn Proxy)
        sem_chap = asyncio.Semaphore(2)

        async def generate_single_chapter(chap_idx: int, chap: Dict[str, Any]):
            chap_title = chap.get('title', f'Chương {chap_idx+1}')
            print(f"[Custom AI] Đang viết chi tiết {chap_title}...")
            chap_prompt = f"""Dựa vào cốt truyện thể loại '{genre}', chủ đề '{topic}'.
Hãy viết kịch bản chi tiết cho Chương {chap.get('chapter', chap_idx+1)}: '{chap_title}' (Nội dung: {chap.get('summary', '')}).
Chia thành {scenes_per_chapter} phân cảnh (scenes) kể chuyện sâu sắc, mỗi cảnh gồm 100-180 từ lời kể tiếng Việt và 1 prompt tiếng Anh miêu tả hình ảnh.
Định dạng trả về:
[
  {{"text": "Lời kể cảnh...", "image_prompt": "English image prompt..."}},
  ...
]
Chỉ trả lời mảng JSON."""
            async with sem_chap:
                for retry in range(2):
                    try:
                        timeout_chap = aiohttp.ClientTimeout(total=45, connect=10)
                        async with aiohttp.ClientSession(timeout=timeout_chap) as session:
                            async with session.post(f"{base_url}/chat/completions", headers=headers, json={
                                "model": model,
                                "messages": [{"role": "user", "content": chap_prompt}],
                                "temperature": 0.8
                            }) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    content = data["choices"][0]["message"]["content"]
                                    m = re.search(r"\[.*\]", content, re.DOTALL)
                                    if m:
                                        sc_list = json.loads(m.group(0))
                                        print(f"[Custom AI] Đã viết xong {chap_title} ({len(sc_list)} phân cảnh)")
                                        return chap_idx, chap, sc_list
                                else:
                                    err_txt = await resp.text()
                                    print(f"[Custom AI] Chương {chap_idx+1} HTTP {resp.status}: {err_txt[:100]}")
                    except Exception as e:
                        print(f"[Custom AI] Lỗi sinh chương {chap_idx+1} (lần {retry+1}): {e}")
                    await asyncio.sleep(1)
            return chap_idx, chap, []

        chap_tasks = [generate_single_chapter(i, chap) for i, chap in enumerate(chapters_outline)]
        chap_results = await asyncio.gather(*chap_tasks, return_exceptions=True)

        all_scenes = []
        scene_counter = 1
        for res in chap_results:
            if isinstance(res, tuple) and len(res) == 3:
                _, chap, chap_scenes = res
                if isinstance(chap_scenes, list):
                    for sc in chap_scenes:
                        all_scenes.append({
                            "scene": scene_counter,
                            "text": f"[{chap.get('title')}] {sc.get('text')}" if scene_counter % scenes_per_chapter == 1 else sc.get('text'),
                            "image_prompt": sc.get('image_prompt', 'cinematic atmosphere, highly detailed')
                        })
                        scene_counter += 1

        if all_scenes:
            print(f"[Custom AI] Hoàn tất toàn bộ kịch bản: Tổng cộng {len(all_scenes)} phân cảnh!")
            return all_scenes

        return await self._generate_story_pollinations_or_fallback(genre, topic, total_scenes)

    async def _generate_story_pollinations_or_fallback(
        self,
        genre: str,
        topic: str,
        num_scenes: int
    ) -> List[Dict[str, Any]]:
        """Sinh truyện qua Pollinations AI hoặc template có sẵn"""
        prompt = f"""Hãy viết một câu chuyện audio thể loại '{genre}', chủ đề '{topic}' gồm {num_scenes} phân cảnh.
Mỗi phân cảnh gồm 'scene' (int), 'text' (tiếng Việt), 'image_prompt' (tiếng Anh).
Trả về JSON Array:
[
  {{"scene": 1, "text": "...", "image_prompt": "..."}},
  ...
]
Chỉ trả về JSON Array."""

        try:
            url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}?json=true"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=45)) as resp:
                    if resp.status == 200:
                        text_resp = await resp.text()
                        json_match = re.search(r"\[.*\]", text_resp, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group(0))
        except Exception:
            pass

        return self._generate_fallback_story(genre, topic, num_scenes)

    def parse_raw_text_to_scenes(
        self,
        raw_text: str,
        style_key: str = "dark_mystery",
        max_words_per_scene: int = 55
    ) -> List[Dict[str, Any]]:
        """
        Phân tách văn bản truyện dài thành các Scene hợp lý kèm Khóa Nhân vật & Bối cảnh (Consistency Anchor)
        """
        paragraphs = [p.strip() for p in raw_text.split("\n") if p.strip()]
        chunks = []

        for p in paragraphs:
            sentences = re.split(r'(?<=[.!?…])\s+', p)
            current_chunk = []
            current_count = 0

            for s in sentences:
                words = s.split()
                if current_count + len(words) > max_words_per_scene and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [s]
                    current_count = len(words)
                else:
                    current_chunk.append(s)
                    current_count += len(words)

            if current_chunk:
                chunks.append(" ".join(current_chunk))

        scenes = []
        for idx, chunk in enumerate(chunks, start=1):
            image_prompt = self._generate_scene_image_prompt(chunk, idx, style_key)
            scenes.append({
                "scene": idx,
                "text": chunk,
                "image_prompt": image_prompt
            })

        return scenes

    def _generate_scene_image_prompt(self, vietnamese_text: str, scene_idx: int, style_key: str) -> str:
        keywords_map = {
            "rừng": "ancient dark pine forest, towering foggy trees, moonlight through branches",
            "nhà": "isolated eerie wooden cabin, glowing warm window, dark moody night",
            "mưa": "heavy torrential rain, wet reflection on ground, lightning in distance",
            "đêm": "midnight sky, starry night, mystical moonlight, silhouettes",
            "núi": "majestic misty mountains, floating clouds, epic landscape",
            "biển": "stormy dark ocean waves, lighthouse light in fog",
            "đèn": "vintage lantern glowing, mystical warm light, deep shadows",
            "hoa": "falling cherry blossom petals, serene romantic scenery",
            "phòng": "cozy aesthetic vintage bedroom, bookshelves, soft candle light",
            "cửa sổ": "rain drops on window glass, looking outside at mysterious street",
            "kiếm": "ancient warrior holding sword, epic misty battlefield, martial arts",
            "chùa": "ancient oriental temple on mountain peak, incense smoke, mystical",
            "thành phố": "cyberpunk neon city streets at night, wet asphalt, glowing signs"
        }

        found_prompts = []
        lower_text = vietnamese_text.lower()
        for kw, prompt_desc in keywords_map.items():
            if kw in lower_text:
                found_prompts.append(prompt_desc)

        if not found_prompts:
            found_prompts.append("mysterious cinematic scenery, atmospheric moody lighting, depth of field")

        return ", ".join(found_prompts[:3])

    def _generate_fallback_story(self, genre: str, topic: str, num_scenes: int) -> List[Dict[str, str]]:
        templates = {
            "dark_mystery": [
                {"scene": 1, "text": "Màn đêm buông xuống, sương mù dày đặc bao trùm lấy con đường mòn dẫn vào rừng sâu. Nơi đây dường như thời gian đã ngừng trôi.", "image_prompt": "foggy mysterious dirt road leading into dark dense forest, eerie moonlight, cinematic"},
                {"scene": 2, "text": "Từ phía xa, một căn nhà gỗ cổ kính hiện ra với ánh đèn vàng leo lét le lói qua khung cửa sổ bám đầy bụi thời gian.", "image_prompt": "ancient wooden cabin in the deep woods, glowing warm window, misty night, photorealistic"},
                {"scene": 3, "text": "Tiếng gió rít qua từng khe cửa, hòa cùng tiếng bước chân lạo xạo trên lá khô khiến không gian càng thêm rùng rợn.", "image_prompt": "creepy dark hallway inside old cabin, vintage wooden door slightly open, moonlight shadow"},
                {"scene": 4, "text": "Một bức thư cũ ố vàng nằm trên bàn, hé lộ bí mật kinh hoàng đã bị chôn vùi suốt hơn hai mươi năm qua.", "image_prompt": "antique yellowed letter on wooden table, vintage candle burning, dramatic moody lighting"},
                {"scene": 5, "text": "Bóng đen bí ẩn bỗng vụt qua ngoài hiên, để lại sự tĩnh lặng đến lạnh gáy và câu hỏi không lời đáp.", "image_prompt": "silhouette of mysterious figure outside window in thick fog, dark horror atmosphere, 8k"}
            ],
            "romantic_lofi": [
                {"scene": 1, "text": "Chiều muộn mùa thu, những giọt mưa rả rích gõ nhịp trên khung cửa kính, mang theo chút se lạnh và những nỗi niềm vương vấn.", "image_prompt": "rain drops on cozy window, aesthetic autumn city view, lofi anime aesthetic, soft lighting"},
                {"scene": 2, "text": "Tách cà phê ấm bốc khói nhẹ bên cuốn sách mở dở, từng giai điệu mộc mạc vang lên gợi nhớ về những kỷ niệm xưa cũ.", "image_prompt": "steaming coffee cup next to open vintage book, warm soft room lighting, Makoto Shinkai style"},
                {"scene": 3, "text": "Có những ngày ta chỉ muốn dừng lại, lắng nghe nhịp thở của thành phố và tìm kiếm sự an yên trong tâm hồn.", "image_prompt": "peaceful aesthetic bedroom at dusk, warm lamp, cozy atmosphere, anime scenery"},
                {"scene": 4, "text": "Dù ngoài kia cuộc sống có hối hả, hy vọng bạn vẫn luôn giữ được một góc bình yên cho riêng mình.", "image_prompt": "sunset glowing through window curtains, golden hour, serene peaceful mood, 4k"}
            ]
        }

        genre_scenes = templates.get(genre, templates["dark_mystery"])
        result = []
        for i in range(num_scenes):
            src_idx = i % len(genre_scenes)
            item = dict(genre_scenes[src_idx])
            item["scene"] = i + 1
            result.append(item)
        return result

    async def generate_video_description(
        self,
        title: str,
        genre: str = "dark_mystery",
        topic: str = "",
        scenes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Tự động tạo Mô tả Video YouTube chuẩn SEO chuyên nghiệp:
        - Tóm tắt câu chuyện kịch tính (Hook & Synopsis)
        - Mốc thời gian Timeline / Chapters
        - Hashtags thịnh hành (#TruyenAudio #ReviewPhim...)
        - Danh sách Tags SEO
        - Lời kêu gọi đăng ký kênh & Bản quyền
        """
        settings = load_settings()
        api_key = settings.get("api_key", "").strip()
        base_url = settings.get("base_url", "https://api.openai.com/v1").strip().rstrip("/")
        model = settings.get("chat_model", "gpt-4o-mini").strip()

        # Tạo trích đoạn nội dung
        story_summary_text = ""
        if scenes and len(scenes) > 0:
            story_summary_text = " ".join([sc.get("text", "") for sc in scenes[:5]])[:600]

        if api_key:
            try:
                system_prompt = (
                    "Bạn là chuyên gia Marketing và Tối ưu SEO kênh YouTube Truyện Audio / Phim ngắn / Podcast triệu view. "
                    "Hãy tạo phần mô tả video (Video Description) hoàn chỉnh, hấp dẫn, kích thích tương tác và chuẩn SEO. "
                    "Định dạng trả về BẮT BUỘC là JSON object thuần túy."
                )
                user_prompt = f"""Hãy viết mô tả video YouTube cho truyện audio:
Tiêu đề: {title}
Thể loại: {genre}
Chủ đề: {topic}
Trích đoạn nội dung: {story_summary_text}

Định dạng JSON cần trả về chính xác:
{{
  "hook": "Câu mở đầu giật gân, cuốn hút 1-2 câu để giữ chân người xem...",
  "synopsis": "Đoạn tóm tắt nội dung kịch tính (khoảng 3-4 câu) gợi mở xung đột và cao trào mà không spoil hết...",
  "chapters": [
    {{"time": "00:00", "title": "Mở đầu - Biến cố bất ngờ"}},
    {{"time": "03:15", "title": "5 Năm cay đắng nơi đất khách"}},
    {{"time": "08:40", "title": "Kế hoạch trả thù hoàn hảo"}},
    {{"time": "14:20", "title": "Cái kết đắt giá cho kẻ phản bội"}}
  ],
  "hashtags": ["#TruyenAudio", "#TruyenKiemHiep", "#ReviewPhim", "#Drama", "#PhimNganHay"],
  "seo_tags": ["truyện audio", "kể chuyện đêm khuya", "audio story", "phim ngắn"],
  "full_formatted_description": "Nội dung đầy đủ đã format đẹp đẽ sẵn sàng copy dán vào YouTube..."
}}"""

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7
                }

                timeout = aiohttp.ClientTimeout(total=30, connect=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(f"{base_url}/chat/completions", headers=headers, json=payload) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            content = data["choices"][0]["message"]["content"].strip()
                            json_match = re.search(r"\{.*\}", content, re.DOTALL)
                            if json_match:
                                return json.loads(json_match.group(0))
            except Exception as e:
                print(f"Lỗi khi tạo mô tả qua AI ({e}), chuyển sang template chuẩn SEO...")

        # Fallback tạo mô tả chuẩn SEO chuyên nghiệp nếu offline
        return self._generate_description_fallback(title, genre, topic, scenes)

    def _generate_description_fallback(
        self,
        title: str,
        genre: str,
        topic: str,
        scenes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Template mô tả chuẩn SEO YouTube cực đẹp"""
        clean_title = title.strip() or "Truyện Audio Đặc Sắc"
        
        hook = f"🔥 {clean_title} - Câu chuyện audio kịch tính và sâu sắc đến từng phút giây!"
        synopsis = (
            f"Chào mừng các bạn đến với tác phẩm audio đặc sắc: '{clean_title}'. "
            f"Một câu chuyện đầy bất ngờ, cảm xúc nghẹn ngào và những nút thắt kịch tính sẽ khiến bạn không thể rời tai. "
            f"Hãy cùng lắng nghe và cảm nhận trọn vẹn câu chuyện nhé!"
        )

        chapters = [
            {"time": "00:00", "title": "Mở đầu câu chuyện"},
            {"time": "02:30", "title": "Nút thắt và biến cố kịch tính"},
            {"time": "06:45", "title": "Cao trào xung đột đỉnh điểm"},
            {"time": "11:20", "title": "Đoạn kết bất ngờ và sâu lắng"}
        ]

        hashtags = ["#TruyenAudio", "#TruyenNgan", "#AudioStory", "#KeChuyenDemKhuya", "#PodcastTruyen", "#Drama"]
        seo_tags = ["truyện audio", "nghe truyện", "kể chuyện đêm khuya", "truyện hay", "audio story việt nam"]

        full_desc = f"""{clean_title}

{hook}

📖 NỘI DUNG TÓM TẮT:
{synopsis}

⏱️ MỐC THỜI GIAN (CHAPTERS):
00:00 - Mở đầu câu chuyện
02:30 - Nút thắt và biến cố kịch tính
06:45 - Cao trào xung đột đỉnh điểm
11:20 - Đoạn kết bất ngờ và sâu lắng

🔔 ĐĂNG KÝ KÊNH ĐỂ ĐÓN NGHE CÁC TẬP MỚI NHẤT MỖI NGÀY!
👉 Like, Comment và Share để ủng hộ kênh phát triển hơn nữa nhé.

---------------------------------------------------
© Bản quyền thuộc về kênh Audio Story AI
#️⃣ HASHTAGS:
{" ".join(hashtags)}
"""
        return {
            "hook": hook,
            "synopsis": synopsis,
            "chapters": chapters,
            "hashtags": hashtags,
            "seo_tags": seo_tags,
            "full_formatted_description": full_desc.strip()
        }

# Instance singleton
story_engine = StoryEngine()
