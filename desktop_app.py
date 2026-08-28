import os
import sys
import time
import socket
import threading
import uvicorn
import urllib.request
from pathlib import Path

# Fix lỗi PyInstaller --windowed khi sys.stdout/stderr là None gây crash uvicorn logging ('NoneType' object has no attribute 'isatty')
class SafeStream:
    def write(self, s):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False

if sys.stdout is None or not hasattr(sys.stdout, 'isatty'):
    sys.stdout = SafeStream()
if sys.stderr is None or not hasattr(sys.stderr, 'isatty'):
    sys.stderr = SafeStream()
if sys.stdin is None or not hasattr(sys.stdin, 'isatty'):
    sys.stdin = SafeStream()

if sys.platform == "win32":
    import io
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass
    if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer is not None:
        try:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass

# Thêm thư mục hiện tại vào sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def find_free_port(default_port=8000):
    """Tìm cổng còn trống để chạy server"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", default_port))
        sock.close()
        return default_port
    except OSError:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

server_error = []

def run_server(port):
    """Chạy FastAPI backend ngầm"""
    try:
        from backend.app import app
        config = uvicorn.Config(
            app=app,
            host="127.0.0.1",
            port=port,
            log_config=None,
            loop="asyncio",
            http="h11"
        )
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        import traceback
        err_msg = f"{str(e)}\n{traceback.format_exc()}"
        server_error.append(err_msg)
        try:
            with open("server_crash.log", "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass

def wait_for_server(port, timeout=15):
    """Chờ server khởi động xong"""
    start_time = time.time()
    url = f"http://127.0.0.1:{port}/api/config"
    while time.time() - start_time < timeout:
        if server_error:
            return False
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False

def show_error_box(title, message):
    """Hiển thị hộp thoại báo lỗi Windows nếu xảy ra sự cố"""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, str(message), str(title), 0x10 | 0x0)
    except Exception:
        pass

def main():
    try:
        port = find_free_port(8000)
        
        # 1. Khởi động server trong luồng ngầm
        server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
        server_thread.start()

        # 2. Chờ server phản hồi
        if not wait_for_server(port):
            err_detail = server_error[0] if server_error else "Hết thời gian chờ kết nối cổng 8000."
            show_error_box("Lỗi Khởi Động Server", f"Không thể khởi động Web Server backend:\n{err_detail}")
            sys.exit(1)

        app_url = f"http://127.0.0.1:{port}"

        # 3. Khởi tạo cửa sổ Desktop Native (pywebview)
        opened_native = False
        try:
            import webview
            window = webview.create_window(
                title="AudioStory Studio - AI Video & YouTube Auto-Pilot",
                url=app_url,
                width=1440,
                height=900,
                min_size=(1024, 700),
                background_color="#0b0f19",
                text_select=True
            )
            webview.start(debug=False)
            opened_native = True
        except Exception as e:
            # Fallback nếu máy tính thiếu Edge WebView2 hoặc pywebview lỗi
            import webbrowser
            webbrowser.open(app_url)
            # Giữ server chạy khi mở qua trình duyệt
            while True:
                time.sleep(1)

    except Exception as e:
        show_error_box("Lỗi Ứng Dụng", f"Đã xảy ra lỗi khi chạy AudioStory Studio:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
