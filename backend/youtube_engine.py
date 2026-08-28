import os
import json
import time
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, Any, Optional, List
from backend.config import BASE_DIR, OUTPUT_DIR, SETTINGS_FILE

YOUTUBE_TOKEN_FILE = BASE_DIR / "youtube_token.json"
YOUTUBE_CLIENT_SECRET_FILE = BASE_DIR / "client_secret.json"

class YouTubeEngine:
    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube"
        ]

    def get_client_credentials(self) -> Dict[str, str]:
        """Đọc thông tin Client ID & Secret từ file hoặc settings"""
        if YOUTUBE_CLIENT_SECRET_FILE.exists():
            try:
                with open(YOUTUBE_CLIENT_SECRET_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    installed = data.get("installed") or data.get("web", {})
                    return {
                        "client_id": installed.get("client_id", ""),
                        "client_secret": installed.get("client_secret", ""),
                        "redirect_uris": installed.get("redirect_uris", ["http://localhost:8000/api/youtube/oauth2callback", "urn:ietf:wg:oauth:2.0:oob"])
                    }
            except Exception:
                pass
        return {"client_id": "", "client_secret": "", "redirect_uris": ["http://localhost:8000/api/youtube/oauth2callback", "urn:ietf:wg:oauth:2.0:oob"]}

    def save_client_credentials(self, client_id: str, client_secret: str):
        """Lưu Client ID & Secret vào file client_secret.json"""
        data = {
            "installed": {
                "client_id": client_id.strip(),
                "client_secret": client_secret.strip(),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8000/api/youtube/oauth2callback", "urn:ietf:wg:oauth:2.0:oob"]
            }
        }
        with open(YOUTUBE_CLIENT_SECRET_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_auth_url(self, client_id: Optional[str] = None, redirect_uri: Optional[str] = None) -> str:
        """Tạo link Google OAuth 2.0 đăng nhập kênh YouTube"""
        creds = self.get_client_credentials()
        cid = client_id or creds.get("client_id")
        if not cid:
            return ""
        
        scope_str = " ".join(self.scopes)
        red_uri = redirect_uri or "http://localhost:8000/api/youtube/oauth2callback"
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={cid}&"
            f"redirect_uri={red_uri}&"
            f"response_type=code&"
            f"scope={scope_str}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        return auth_url

    async def exchange_code_for_token(self, auth_code: str, redirect_uri: str = "http://localhost:8000/api/youtube/oauth2callback") -> Dict[str, Any]:
        """Đổi authorization code lấy Access Token và Refresh Token"""
        creds = self.get_client_credentials()
        payload = {
            "code": auth_code.strip(),
            "client_id": creds.get("client_id"),
            "client_secret": creds.get("client_secret"),
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://oauth2.googleapis.com/token", data=payload) as resp:
                if resp.status == 200:
                    token_data = await resp.json()
                    token_data["created_at"] = time.time()
                    with open(YOUTUBE_TOKEN_FILE, "w", encoding="utf-8") as f:
                        json.dump(token_data, f, indent=2)
                    return token_data
                else:
                    err = await resp.text()
                    raise RuntimeError(f"Lỗi xác thực Google: {err}")

    async def get_valid_access_token(self) -> Optional[str]:
        """Lấy Access Token hợp lệ, tự động refresh nếu hết hạn"""
        if not YOUTUBE_TOKEN_FILE.exists():
            return None

        try:
            with open(YOUTUBE_TOKEN_FILE, "r", encoding="utf-8") as f:
                token_data = json.load(f)
        except Exception:
            return None

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        created_at = token_data.get("created_at", 0)

        # Kiểm tra token còn hạn không (trừ hao 60 giây)
        if time.time() < created_at + expires_in - 60 and access_token:
            return access_token

        # Nếu hết hạn thì làm mới bằng refresh_token
        if refresh_token:
            creds = self.get_client_credentials()
            payload = {
                "client_id": creds.get("client_id"),
                "client_secret": creds.get("client_secret"),
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post("https://oauth2.googleapis.com/token", data=payload) as resp:
                    if resp.status == 200:
                        new_data = await resp.json()
                        token_data["access_token"] = new_data.get("access_token")
                        token_data["expires_in"] = new_data.get("expires_in", 3600)
                        token_data["created_at"] = time.time()
                        with open(YOUTUBE_TOKEN_FILE, "w", encoding="utf-8") as f:
                            json.dump(token_data, f, indent=2)
                        return token_data["access_token"]

        return None

    async def get_channel_info(self) -> Dict[str, Any]:
        """Lấy thông tin kênh YouTube đã liên kết"""
        token = await self.get_valid_access_token()
        if not token:
            return {"connected": False}

        headers = {"Authorization": f"Bearer {token}"}
        url = "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        items = data.get("items", [])
                        if items:
                            ch = items[0]
                            snippet = ch.get("snippet", {})
                            stats = ch.get("statistics", {})
                            return {
                                "connected": True,
                                "id": ch.get("id"),
                                "title": snippet.get("title", ""),
                                "description": snippet.get("description", ""),
                                "custom_url": snippet.get("customUrl", ""),
                                "avatar_url": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                                "subscriber_count": stats.get("subscriberCount", "0"),
                                "video_count": stats.get("videoCount", "0")
                            }
        except Exception:
            pass

        return {"connected": False}

    def disconnect_channel(self):
        """Hủy liên kết kênh YouTube"""
        if YOUTUBE_TOKEN_FILE.exists():
            try:
                YOUTUBE_TOKEN_FILE.unlink()
            except Exception:
                pass

    async def upload_video_to_youtube(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy_status: str = "public",
        thumbnail_path: Optional[str] = None,
        category_id: str = "24", # 24 = Entertainment, 1 = Film & Animation
        publish_at: Optional[str] = None # ISO format e.g. "2026-08-25T19:00:00Z"
    ) -> Dict[str, Any]:
        """
        Tải video lên YouTube hoàn chỉnh qua YouTube Data API v3 Resumable Upload
        """
        token = await self.get_valid_access_token()
        if not token:
            raise RuntimeError("Chưa đăng nhập kênh YouTube. Vui lòng liên kết tài khoản trước.")

        if not Path(video_path).exists():
            raise FileNotFoundError(f"Không tìm thấy file video: {video_path}")

        file_size = Path(video_path).stat().st_size

        # Chuẩn bị Metadata
        metadata = {
            "snippet": {
                "title": title[:100], # YouTube giới hạn tiêu đề 100 ký tự
                "description": description[:5000], # YouTube giới hạn mô tả 5000 ký tự
                "tags": tags or ["TruyenAudio", "AudioStory", "ReviewPhim", "PhimNgan", "Drama"],
                "categoryId": category_id,
                "defaultLanguage": "vi",
                "defaultAudioLanguage": "vi"
            },
            "status": {
                "privacyStatus": privacy_status, # public, private, unlisted
                "selfDeclaredMadeForKids": False
            }
        }

        # Nếu có hẹn giờ công chiếu trên YouTube
        if publish_at and privacy_status == "private":
            metadata["status"]["publishAt"] = publish_at

        # Bước 1: Khởi tạo Resumable Upload Session
        init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
        headers_init = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(file_size),
            "X-Upload-Content-Type": "video/mp4"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(init_url, headers=headers_init, json=metadata) as init_resp:
                if init_resp.status != 200:
                    err_txt = await init_resp.text()
                    raise RuntimeError(f"Lỗi khởi tạo upload YouTube ({init_resp.status}): {err_txt}")

                upload_session_url = init_resp.headers.get("Location")
                if not upload_session_url:
                    raise RuntimeError("Không nhận được Upload Location từ YouTube.")

            # Bước 2: Truyền tệp Video
            headers_upload = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "video/mp4",
                "Content-Length": str(file_size)
            }

            timeout = aiohttp.ClientTimeout(total=600) # Cho phép tải video lớn trong 10 phút
            with open(video_path, "rb") as video_file:
                video_data = video_file.read()

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.put(upload_session_url, headers=headers_upload, data=video_data) as upload_resp:
                    if upload_resp.status in (200, 201):
                        resp_data = await upload_resp.json()
                        video_id = resp_data.get("id")
                        youtube_url = f"https://www.youtube.com/watch?v={video_id}"

                        # Bước 3: Đặt Thumbnail nếu có
                        thumb_success = False
                        if thumbnail_path and Path(thumbnail_path).exists() and video_id:
                            try:
                                thumb_success = await self._upload_thumbnail(token, video_id, thumbnail_path)
                            except Exception as e:
                                print(f"Lỗi khi đặt thumbnail YouTube: {e}")

                        return {
                            "status": "success",
                            "video_id": video_id,
                            "youtube_url": youtube_url,
                            "thumbnail_set": thumb_success,
                            "title": title
                        }
                    else:
                        err_txt = await upload_resp.text()
                        raise RuntimeError(f"Lỗi upload video YouTube ({upload_resp.status}): {err_txt}")

    async def _upload_thumbnail(self, token: str, video_id: str, thumbnail_path: str) -> bool:
        """Đặt Custom Thumbnail cho Video với chuẩn hóa JPEG RGB, tối ưu dung lượng < 1.8MB và tự động thử lại"""
        import io
        from PIL import Image

        thumb_url = f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}"
        
        # 1. Chuẩn hóa ảnh về JPEG chuẩn RGB < 2MB (chuẩn YouTube khuyến nghị 1280x720)
        try:
            with Image.open(thumbnail_path) as im:
                im = im.convert("RGB")
                if im.size != (1280, 720):
                    im = im.resize((1280, 720), Image.Resampling.LANCZOS)
                
                out_io = io.BytesIO()
                im.save(out_io, format="JPEG", quality=88, optimize=True)
                thumb_bytes = out_io.getvalue()
                
                # Nếu vẫn > 1.8MB thì giảm chất lượng xuống để chắc chắn < 2MB
                if len(thumb_bytes) > 1800000:
                    out_io = io.BytesIO()
                    im.save(out_io, format="JPEG", quality=75, optimize=True)
                    thumb_bytes = out_io.getvalue()
        except Exception as e:
            print(f"[YouTube Thumbnail] Lỗi đọc/chuẩn hóa file ảnh: {e}. Đọc file nhị phân trực tiếp...")
            with open(thumbnail_path, "rb") as f:
                thumb_bytes = f.read()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "image/jpeg"
        }

        # 2. Upload với Retry (do đôi khi YouTube cần vài giây để index videoId trước khi nhận thumbnail)
        max_retries = 3
        timeout = aiohttp.ClientTimeout(total=45)
        for attempt in range(1, max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(thumb_url, headers=headers, data=thumb_bytes) as resp:
                        if resp.status in (200, 201):
                            print(f"[YouTube Thumbnail] Đặt thumbnail thành công cho video {video_id}!")
                            return True
                        else:
                            err_txt = await resp.text()
                            print(f"[YouTube Thumbnail] Lần {attempt}/{max_retries} thất bại ({resp.status}): {err_txt[:200]}")
            except Exception as e:
                print(f"[YouTube Thumbnail] Lỗi kết nối lần {attempt}: {e}")
            
            if attempt < max_retries:
                await asyncio.sleep(2 * attempt)

        return False

youtube_engine = YouTubeEngine()
