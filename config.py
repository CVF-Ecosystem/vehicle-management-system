# config.py

# --- Cấu hình file ---
DB_FILE = "vehicle_management_v3.0"
CONFIG_FILE = "config.ini"
LOGS_DIR = "logs"
ARCHIVES_DIR = "archives"
OWNER_MAP_FILE = "owner_map.json"

# --- Thông tin ứng dụng ---
APP_NAME = "Phần mềm Quản lý xe"
APP_VERSION = "V5.0"

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


