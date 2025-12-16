# utils.py
import logging
from logging.handlers import RotatingFileHandler
import configparser
import os
import json
from datetime import datetime
from config import CONFIG_FILE, LOGS_DIR, OWNER_MAP_FILE

def setup_logging(gui_handler=None):
    """Thiết lập hệ thống logging, ghi ra file và có thể cả giao diện."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file_path = os.path.join(LOGS_DIR, "vehicle_app.log")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = RotatingFileHandler(log_file_path, maxBytes=1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    if gui_handler:
        gui_handler.setFormatter(formatter)
        root_logger.addHandler(gui_handler)

def load_config():
    """Đọc file cấu hình .ini hoặc tạo mới nếu chưa có."""
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config["Settings"] = {"language": "vi", "theme": "System"}
        config["Paths"] = {"voucher_template_path": ""}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            config.write(f)
    else:
        config.read(CONFIG_FILE, encoding="utf-8")
        if not config.has_section("Paths"):
            config.add_section("Paths")
            
    return config

def save_config(config):
    """Lưu lại các thay đổi vào file cấu hình .ini."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        config.write(f)

def get_default_filename(base_name, extension):
    """
    Tạo một tên file mặc định dựa trên tên cơ sở và ngày hiện tại.
    Ví dụ: "Danh_sach_ton_19.10.2025.xlsx"
    """
    date_str = datetime.now().strftime("%d.%m.%Y")
    safe_base_name = "".join(c for c in base_name if c.isalnum() or c in " _-").rstrip()
    return f"{safe_base_name}_{date_str}{extension}"

def format_datetime_for_display(iso_string: str) -> str:
    """
    Chuyển đổi một chuỗi ngày giờ ISO 8601 thành định dạng dd/mm/yyyy HH:MM.
    Trả về chuỗi rỗng nếu đầu vào không hợp lệ.
    """
    if not iso_string:
        return ""
    try:
        dt_object = datetime.fromisoformat(iso_string)
        return dt_object.strftime('%d/%m/%Y %H:%M')
    except (ValueError, TypeError):
        return ""

class GUILoggingHandler(logging.Handler):
    """Một handler tùy chỉnh để chuyển hướng log ra một widget Textbox của CustomTkinter."""
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        try:
            self.widget.configure(state="normal")
            self.widget.delete("1.0", "end")
            self.widget.configure(state="disabled")
        except Exception:
            pass

    def emit(self, record):
        msg = self.format(record)
        try:
            if self.widget.winfo_exists():
                self.widget.after(0, self._write_log, msg)
        except Exception:
            pass

    def _write_log(self, msg):
        """Hàm ghi log vào widget, được bao bọc bởi try-except để tăng độ ổn định."""
        try:
            if self.widget.winfo_exists():
                self.widget.configure(state="normal")
                self.widget.insert("end", msg + "\n")
                self.widget.see("end")
                self.widget.configure(state="disabled")
        except Exception:
            pass