# ui/web_dashboard_manager.py
"""
Web Dashboard Manager — Quản lý Streamlit web dashboard.

Tách từ main.py để giảm kích thước God class InventoryApp (7.1-ARCH-1).
"""

import logging
import os
import socket
import subprocess
import threading
import webbrowser

logger = logging.getLogger(__name__)


class WebDashboardManager:
    """
    Quản lý vòng đời của Streamlit web dashboard.
    
    Tách biệt logic web dashboard khỏi InventoryApp để:
    - Dễ test độc lập
    - Giảm kích thước main.py
    - Dễ thay thế Streamlit bằng framework khác
    """

    def __init__(self, app_instance):
        """
        Args:
            app_instance: InventoryApp instance (để gọi show_toast, status_var, etc.)
        """
        self.app = app_instance
        self._process = None
        self._port = None

    @property
    def is_running(self) -> bool:
        """Kiểm tra dashboard có đang chạy không."""
        return self._process is not None and self._process.poll() is None

    def find_free_port(self, start_port: int = 8501, max_attempts: int = 10) -> int | None:
        """Tìm port trống để chạy Streamlit."""
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("localhost", port))
                    return port
            except OSError:
                continue
        return None

    def launch(self):
        """Khởi động Web Dashboard (Streamlit)."""
        if self.is_running:
            url = f"http://localhost:{self._port}"
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

        thread = threading.Thread(target=self._run_streamlit, daemon=True)
        thread.start()

    def _run_streamlit(self):
        """Chạy Streamlit trong background thread."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # web_dashboard.py nằm ở project root, không phải ui/
            dashboard_path = os.path.join(os.path.dirname(script_dir), "web_dashboard.py")

            if not os.path.exists(dashboard_path):
                self.app.after(
                    0,
                    lambda: self._on_error(f"Không tìm thấy file: {dashboard_path}")
                )
                return

            cmd = [
                "streamlit", "run", dashboard_path,
                "--server.port", str(self._port),
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false",
                "--server.address", "localhost",
            ]

            startupinfo = None
            creationflags = 0
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=creationflags,
                cwd=os.path.dirname(script_dir),
            )

            url = f"http://localhost:{self._port}"

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

        except FileNotFoundError:
            self.app.after(
                0,
                lambda: self._on_error(
                    "Streamlit chưa được cài đặt. Hãy chạy: pip install streamlit plotly"
                ),
            )
        except Exception as e:
            self.app.after(0, lambda: self._on_error(str(e)))

    def _on_started(self, url: str):
        """Callback khi Streamlit đã khởi động."""
        msg = self.app.get_translation("web_dashboard_started").format(url=url)
        self.app.status_var.set(msg)
        self.app.show_toast(msg)
        logger.info(f"Web Dashboard started at {url}")
        self._update_buttons()
        webbrowser.open(url)

    def _on_error(self, error: str):
        """Callback khi có lỗi khởi động Streamlit."""
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
