# SOFT QUẢN LÝ XE 5.0

Ứng dụng quản lý xe theo luồng: Nhập bãi → Phiếu xuất (Dispatch) → Xuất bãi → Tồn kho/Tìm kiếm/Báo cáo.

## 1) Yêu cầu môi trường

- Windows
- Python 3.11+ (khuyến nghị 3.11.x)
- Quyền ghi file trong thư mục dự án (để tạo DB/logs/archives)

## 2) Cài đặt

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 3) Chạy ứng dụng

```bash
python main.py
```

## 4) Cấu trúc dự án (tóm tắt)

```text
archives/                    # File CSDL lưu trữ (archive)
assets/                      # Tài nguyên
config/                      # Cấu hình bổ sung
database/                    # Layer thao tác SQLite (schema + managers)
  __init__.py
  base_manager.py
  vehicle_manager.py
  entity_manager.py
  dispatch_manager.py
  location_manager.py
icons/                       # Icons
logs/                        # Log runtime
report_generators/           # Xuất báo cáo (Excel/PDF/Word)
ui/                          # Giao diện (CustomTkinter)

main.py                      # Entrypoint
config.py                    # Hằng số & cấu hình chung (APP_VERSION, cột Excel, ...)
config.ini                   # Cấu hình người dùng (ngôn ngữ/theme/template...)
utils.py                     # Tiện ích chung (logging, config...)
translations.py              # Đa ngôn ngữ
excel_importer.py            # Import Excel
owner_map.json               # Map tên chủ hàng
requirements.txt             # Phụ thuộc Python (pinned)
```

## 5) CSDL (SQLite)

- File DB được tạo/tái sử dụng theo `DB_FILE` trong `config.py`.
- Tính năng lưu trữ (archive) ghi sang `archives/<...>_ARCHIVE.db`.

## 6) Log

- Log runtime được ghi vào thư mục `logs/` (xem hàm `setup_logging` trong `utils.py`).
