# ui/web_dashboard_manager.py
"""
Web Dashboard Manager — Quản lý Flask web dashboard.

Tách từ main.py để giảm kích thước God class InventoryApp (7.1-ARCH-1).
"""

import logging
import os
import secrets
import socket
import subprocess
import threading
import webbrowser

logger = logging.getLogger(__name__)


class WebDashboardManager:
    """
    Quản lý vòng đời của Flask web dashboard (dashboard_api.py).
    
    Tách biệt logic web dashboard khỏi InventoryApp để:
    - Dễ test độc lập
    - Giảm kích thước main.py
    - Dễ thay thế backend nếu cần
    """

    def __init__(self, app_instance):
        """
        Args:
            app_instance: InventoryApp instance (để gọi show_toast, status_var, etc.)
        """
        self.app = app_instance
        self._process = None
        self._port = None
        self._session_token: str = self._load_or_create_token()

    def _load_or_create_token(self) -> str:
        """Load token từ file nếu có — tránh invalidate browser tabs khi restart app."""
        try:
            import config as _cfg
            token_path = _cfg.get_data_path("config/dashboard_token.txt")
            if os.path.exists(token_path):
                with open(token_path, "r") as f:
                    token = f.read().strip()
                    if len(token) >= 32:
                        return token
            token = secrets.token_urlsafe(32)
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            with open(token_path, "w") as f:
                f.write(token)
            return token
        except Exception:
            return secrets.token_urlsafe(32)

    @property
    def is_running(self) -> bool:
        """Kiểm tra dashboard có đang chạy không."""
        return self._process is not None and self._process.poll() is None

    def find_free_port(self, start_port: int = None, max_attempts: int = 10) -> int | None:
        """Tìm port trống để chạy Flask dashboard."""
        if start_port is None:
            import config as _cfg
            start_port = _cfg.DASHBOARD_PORT
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("localhost", port))
                    return port
            except OSError:
                continue
        return None

    def launch(self):
        """Khởi động Web Dashboard (Flask)."""
        if self.is_running:
            url = f"http://localhost:{self._port}?token={self._session_token}"
            msg = self.app.get_translation("web_dashboard_already_running").format(url=url)
            self.app.show_toast(msg)
            webbrowser.open(url)
            return

        port = self.find_free_port()
        if not port:
            from tkinter import messagebox
            messagebox.showerror("Error", "Không tìm được port trống để chạy Web Dashboard")
            return

        self._port = port
        self.app.status_var.set(self.app.get_translation("web_dashboard_starting"))
        self.app.update_idletasks()

        thread = threading.Thread(target=self._run_flask, daemon=True)
        thread.start()

    def _run_flask(self):
        """Chạy Flask dashboard_api.py trong background thread."""
        try:
            import sys
            import os

            # Giải quyết đường dẫn dashboard_api.py trong môi trường PyInstaller
            if hasattr(sys, '_MEIPASS'):
                # Chạy dưới dạng EXE — dashboard_api.py nằm cạnh file EXE
                base_dir = os.path.dirname(sys.executable)
                # sys.executable là file .exe, KHÔNG phải python.exe → tìm Python hệ thống
                import shutil
                python_exe = (
                    shutil.which("python")
                    or shutil.which("python3")
                    or shutil.which("py")
                    or "python"
                )
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                base_dir = os.path.dirname(script_dir)
                python_exe = sys.executable

            dashboard_path = os.path.join(base_dir, "dashboard_api.py")

            if not os.path.exists(dashboard_path):
                self.app.after(
                    0,
                    lambda: self._on_error(f"Không tìm thấy file: {dashboard_path}")
                )
                return

            cmd = [python_exe, dashboard_path]

            startupinfo = None
            creationflags = 0
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW
                
            env = os.environ.copy()
            import config
            from config import APP_VERSION_DISPLAY
            env['VEHICLE_APP_DB_PATH'] = config.get_data_path("vehicle_management_v1.0.db")
            env['VEHICLE_APP_VERSION'] = APP_VERSION_DISPLAY
            env['VEHICLE_DASH_PORT']   = str(self._port)
            env['VEHICLE_DASH_TOKEN']  = self._session_token
            
            # --- FIX: PyInstaller DLL Conflict ---
            # PyInstaller thêm _MEIPASS vào biến PATH. Khi gọi subprocess chạy bằng một phiên bản Python khác (v.d global streamlit),
            # nó sẽ vô tình load nhầm file .dll của Python 3.12 (có trong _MEIPASS), gây lỗi "conflicts with this version of Python".
            # Giải pháp: Xoá _MEIPASS khỏi biến môi trường PATH trước khi gọi Popen.
            if hasattr(sys, '_MEIPASS'):
                path_env = env.get('PATH', '')
                env['PATH'] = os.pathsep.join([p for p in path_env.split(os.pathsep) if p.strip().lower() != sys._MEIPASS.lower()])
            # -------------------------------------

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=creationflags,
                cwd=base_dir,
                env=env,
            )

            url = f"http://localhost:{self._port}?token={self._session_token}"

            # Poll until server is ready (max 10 seconds)
            import time
            max_wait = 10
            poll_interval = 0.5
            elapsed = 0
            server_ready = False

            while elapsed < max_wait:
                if self._process.poll() is not None:
                    break
                try:
                    with socket.create_connection(("localhost", self._port), timeout=0.5):
                        server_ready = True
                        break
                except OSError:
                    pass
                time.sleep(poll_interval)
                elapsed += poll_interval

            if server_ready:
                self.app.after(0, lambda: self._on_started(url))
            elif self._process.poll() is not None:
                stderr = self._process.stderr.read().decode("utf-8", errors="ignore")
                self.app.after(0, lambda: self._on_error(stderr))
            else:
                # Timeout but process still running — assume started
                self.app.after(0, lambda: self._on_started(url))

        except Exception as e:
            self.app.after(0, lambda: self._on_error(str(e)))

    def _on_started(self, url: str):
        """Callback khi Flask dashboard đã khởi động."""
        msg = self.app.get_translation("web_dashboard_started").format(url=url)
        self.app.status_var.set(msg)
        self.app.show_toast(msg)
        logger.info(f"Web Dashboard started at {url}")
        self._update_buttons()
        webbrowser.open(url)

    def _on_error(self, error: str):
        """Callback khi có lỗi khởi động Flask dashboard."""
        from tkinter import messagebox
        msg = self.app.get_translation("web_dashboard_error").format(error=error)
        self.app.status_var.set(self.app.get_translation("status_ready"))
        messagebox.showerror("Web Dashboard Error", msg)
        logger.error(f"Web Dashboard error: {error}")

    def stop(self):
        """Dừng Web Dashboard."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            finally:
                self._process = None
                self._port = None
                self.app.show_toast(self.app.get_translation("web_dashboard_stopped"))
                logger.info("Web Dashboard stopped")
                self._update_buttons()

    def _update_buttons(self):
        """Cập nhật trạng thái nút Web Dashboard trên UI."""
        if not hasattr(self.app, "web_dashboard_btn"):
            return

        if self.is_running:
            self.app.web_dashboard_btn.configure(
                text="🌐 Mở Dashboard",
                fg_color="#27ae60",
                hover_color="#2ecc71",
            )
            if hasattr(self.app, "web_stop_btn"):
                self.app.web_stop_btn.pack(pady=(0, 5))
        else:
            self.app.web_dashboard_btn.configure(
                text="🌐 Web Dashboard",
                fg_color="#2980b9",
                hover_color="#3498db",
            )
            if hasattr(self.app, "web_stop_btn"):
                self.app.web_stop_btn.pack_forget()
