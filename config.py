# config.py


import sys, os
def get_resource_path(relative_path):
	if hasattr(sys, '_MEIPASS'):
		base_path = sys._MEIPASS
	else:
		base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
	return os.path.join(base_path, relative_path)

def get_data_path(relative_path):
	# Sử dụng thư mục chứa file exe để lưu dữ liệu (DB, Config, Logs) thay vì thư mục tạm _MEIPASS
	if hasattr(sys, '_MEIPASS'):
		base_path = os.path.dirname(sys.executable)
	else:
		base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
	full_path = os.path.join(base_path, relative_path)
	os.makedirs(os.path.dirname(full_path), exist_ok=True)
	return full_path

# --- Cấu hình file ---
DB_FILE = get_data_path("vehicle_management_v1.0.db")
# Database riêng cho đăng nhập/audit (tách với DB xe)
# Đặt trong thư mục config để dễ quản lý/backup.
SECURITY_DB_FILE = get_data_path("config/security.db")
# Audit logs mặc định ghi vào security DB
AUDIT_DB_FILE = SECURITY_DB_FILE
CONFIG_FILE = get_data_path("config/config.ini")
LOGS_DIR = get_data_path("logs")
ARCHIVES_DIR = get_data_path("archives")
# Owner name normalization map - chuẩn hóa tên chủ hàng
OWNER_MAP_FILE = get_data_path("config/owner_map.json")

# CONFIGURABILITY FIX Issue #15: Configurable backup location
# Can be overridden via environment variable: BACKUP_DIR
BACKUP_DIR = os.getenv("BACKUP_DIR", get_data_path("backups"))

# --- Thông tin ứng dụng ---
APP_NAME = "Phần mềm Quản lý xe"
APP_VERSION = "1.0 @2026"  # Phiên bản kỹ thuật, có thể dùng để kiểm tra tương thích dữ liệu
APP_VERSION_DISPLAY = "V1.0 @2026"  # Chuỗi hiển thị cho người dùng

# --- Hằng số nghiệp vụ ---
STATUS_IN_STOCK = "IN_STOCK"
STATUS_SHIPPED = "SHIPPED"

STATUS_SHIPMENT_OPEN = "OPEN"
STATUS_SHIPMENT_COMPLETED = "COMPLETED"

ENTITY_TYPE_DRIVER = "driver"
ENTITY_TYPE_TRANSPORT = "transport_vehicle"

# --- Hằng số giao diện ---
PAD_GENERAL = 10
PAD_SMALL = 5

# --- Cấu hình cột Excel ---
# Dùng cho import xe
EXPECTED_VIN_COL = "SO KHUNG"
EXPECTED_OWNER_COL = "CHU HANG"
EXPECTED_TYPE_COL = "LOAI XE"

# Dùng cho import layout bãi xe
EXPECTED_BLOCK_COL = "BLOCK"
EXPECTED_ROW_COL = "ROW"
EXPECTED_SLOT_COL = "SLOT"

# Dùng cho import/export Tài xế & Xe VC
EXPECTED_DRIVER_NAME_COL = "TEN TAI XE"
EXPECTED_DRIVER_PHONE_COL = "SO DIEN THOAI"
EXPECTED_DRIVER_CCCD_COL = "SO CCCD" # Bổ sung mới
EXPECTED_PLATE_COL = "BIEN SO XE"
EXPECTED_TRANSPORT_TYPE_COL = "LOAI XE VC"
EXPECTED_NOTES_COL = "GHI CHU"

# --- BỔ SUNG: Cấu hình Font chữ ---
FONT_FAMILY = "Segoe UI" # Hoặc "Arial", "Calibri"... tùy theo sở thích
FONT_SIZE_NORMAL = 13
FONT_SIZE_LARGE = 16
FONT_SIZE_SMALL = 10
FONT_SIZE_TINY = 9
FONT_WEIGHT_BOLD = "bold"
FONT_WEIGHT_NORMAL = "normal"
FONT_WEIGHT_ITALIC = "italic"

DEFAULT_DATE_FORMAT = "DD/MM/YYYY"   # cấu hình chung toàn hệ thống
DEFAULT_TIME_FORMAT = "HH:mm"        # cấu hình chung toàn hệ thống

# --- Phase 3 automation/reporting defaults ---
# Các thư mục mặc định cho auto-import và xuất báo cáo
AUTOMATION_MONITOR_FOLDER = os.getenv("AUTOMATION_MONITOR_FOLDER", get_data_path("data/monitor"))
AUTOMATION_IMPORT_FOLDER = os.getenv("AUTOMATION_IMPORT_FOLDER", get_data_path("data/imports"))
AUTOMATION_LOG_FOLDER = os.getenv("AUTOMATION_LOG_FOLDER", get_data_path("logs/automation"))
AUTOMATION_TASK_TIME = os.getenv("AUTOMATION_TASK_TIME", "02:00")  # Task Scheduler daily time

DEFAULT_EXPORT_FOLDER = os.getenv("DEFAULT_EXPORT_FOLDER", get_data_path("exports"))
DEFAULT_IMPORT_FOLDER = os.getenv("DEFAULT_IMPORT_FOLDER", get_data_path("imports"))

# --- Web Dashboard ---
DASHBOARD_PORT: int = 8502

# --- Audit Log Retention ---
AUDIT_LOG_RETENTION_DAYS: int = 365  # Số ngày giữ audit log trước khi archive

# --- VIN Validation ---
# True = Bắt buộc VIN đúng 17 ký tự + checksum hợp lệ (theo chuẩn ISO 3779)
# False = Chấp nhận VIN từ 6-17 ký tự, không kiểm tra checksum (có cảnh báo)
VIN_STRICT_MODE = False
# VIN_STRICT_MODE = True  # Bỏ comment dòng này khi muốn bắt buộc VIN chuẩn 17 ký tự


