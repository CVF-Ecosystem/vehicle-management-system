# utils.py
import logging
from logging.handlers import RotatingFileHandler
import configparser
import os
from datetime import datetime
from uuid import uuid4
from typing import Optional
from config import CONFIG_FILE, LOGS_DIR, OWNER_MAP_FILE

# Module-level logger
logger = logging.getLogger(__name__)

def setup_logging(gui_handler: Optional[logging.Handler] = None, log_level: int = logging.INFO) -> None:
    """
    Thiết lập hệ thống logging chuẩn hóa.
    
    Features:
    - Rotating file handler (1MB max, 5 backup files)
    - Console handler cho development
    - GUI handler cho hiển thị trong ứng dụng
    - Format chuẩn với timestamp, level, module name, và message
    
    Args:
        gui_handler: Optional handler để gửi logs đến GUI widget
        log_level: Mức log mặc định (default: INFO)
    """
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file_path = os.path.join(LOGS_DIR, "vehicle_app.log")

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers để tránh duplicate
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Format chuẩn hóa: timestamp [LEVEL] module_name - message
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)8s] %(module)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler với rotation
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=1024*1024,  # 1MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)

    # GUI handler nếu có
    if gui_handler:
        gui_handler.setFormatter(formatter)
        gui_handler.setLevel(log_level)
        root_logger.addHandler(gui_handler)
    
    logger.info("Logging system initialized")

def get_logger(name: str) -> logging.Logger:
    """
    Lấy logger cho một module cụ thể.
    
    Usage:
        from utils import get_logger
        logger = get_logger(__name__)
        logger.info("Message")
    
    Args:
        name: Tên module (thường là __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def load_config() -> configparser.ConfigParser:
    """Đọc file cấu hình .ini hoặc tạo mới nếu chưa có."""
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config["Settings"] = {"language": "vi", "theme": "System"}
        config["Paths"] = {"voucher_template_path": ""}
        config["Site"] = {"site_code": "SITE_001", "site_instance_id": str(uuid4())}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            config.write(f)
    else:
        config.read(CONFIG_FILE, encoding="utf-8")
        if not config.has_section("Paths"):
            config.add_section("Paths")
        if not config.has_section("Site"):
            config.add_section("Site")
        if not config.has_option("Site", "site_code"):
            config.set("Site", "site_code", "SITE_001")

        if not config.has_option("Site", "site_instance_id"):
            config.set("Site", "site_instance_id", str(uuid4()))
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                config.write(f)
            
    return config

def save_config(config: configparser.ConfigParser) -> None:
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