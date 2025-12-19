# 🚗 DEVELOPMENT ROADMAP - PHẦN MỀM QUẢN LÝ XE V5.0

> **Tài liệu này mô tả chi tiết lộ trình phát triển và cấu trúc dự án**
>
> Ngày tạo: 17/12/2025
> Cập nhật: 19/12/2025
> Phiên bản hiện tại: V5.1.0-beta
> Phiên bản mục tiêu: V6.0

---

## 📁 CẤU TRÚC THƯ MỤC HIỆN TẠI

```text
SOFT QUAN LY XE 5.0/
│
├── 📄 main.py                      # Entry point - Khởi tạo ứng dụng chính
├── 📄 config.py                    # Hằng số và cấu hình ứng dụng
├── 📄 config.ini                   # File cấu hình người dùng (ngôn ngữ, theme)
├── 📄 translations.py              # Hệ thống đa ngôn ngữ (VI/EN)
├── 📄 utils.py                     # Các hàm tiện ích chung
├── 📄 data_normalizer.py           # Chuẩn hóa dữ liệu đầu vào (VIN, Owner)
├── 📄 api_client.py                # Facade cho Data Access Layer
├── 📄 layout_manager.py            # Logic quản lý layout bãi xe
├── 📄 excel_importer.py            # Import xe hàng loạt từ Excel
├── 📄 voucher_generator.py         # Tạo phiếu vận chuyển
├── 📄 owner_map.json               # Map chuẩn hóa tên chủ hàng
├── 📄 requirements.txt             # Dependencies
├── 📄 README.md                    # Hướng dẫn kỹ thuật
├── 📄 User_Guide.md                # Hướng dẫn sử dụng
│
├── 📂 database/                    # Database Access Layer
│   ├── __init__.py
│   ├── base_manager.py             # Singleton DB connection, Schema setup
│   ├── vehicle_manager.py          # CRUD cho bảng vehicles
│   ├── entity_manager.py           # Quản lý Tài xế, Xe vận chuyển
│   ├── dispatch_manager.py         # Quản lý Phiếu xuất (dispatches)
│   └── location_manager.py         # Quản lý Vị trí bãi xe
│
├── 📂 ui/                          # User Interface Layer
│   ├── __init__.py
│   ├── components.py               # Reusable widgets (Toast, Dialogs)
│   ├── inbound_tab.py              # Tab Nhập bãi
│   ├── outbound_tab.py             # Tab Xuất bãi (lẻ)
│   ├── dispatch_tab.py             # Tab Xuất bãi (nhiều)
│   ├── stock_tab.py                # Tab Tồn bãi
│   ├── search_tab.py               # Tab Tra cứu
│   ├── dashboard_tab.py            # Tab Báo cáo/Thống kê
│   ├── log_tab.py                  # Tab Nhật ký hoạt động
│   ├── camera_scanner.py           # Dialog quét QR Code
│   ├── management_dialogs.py       # Dialogs quản lý Tài xế, Xe VC
│   ├── layout_management_dialog.py # Dialog quản lý Layout bãi
│   ├── voucher_creation_dialog.py  # Dialog tạo phiếu vận chuyển
│   └── archive_explorer_dialog.py  # Dialog tra cứu dữ liệu lưu trữ
│
├── 📂 report_generators/           # Tạo báo cáo
│   ├── excel_generator.py          # Xuất Excel
│   ├── pdf_generator.py            # Xuất PDF, QR Code
│   └── word_generator.py           # Xuất Word (Phiếu VC)
│
├── 📂 assets/                      # Tài nguyên tĩnh
│   ├── Arial.ttf                   # Font chữ
│   ├── Arialbd.ttf                 # Font chữ đậm
│   └── Logo.jpg                    # Logo công ty
│
├── 📂 config/                      # Thư mục cấu hình bổ sung
│   └── config.ini
│
├── 📂 icons/                       # Icons cho UI
│
├── 📂 logs/                        # File log hoạt động
│   └── vehicle_app.log
│
├── 📂 archives/                    # Dữ liệu đã lưu trữ
│
└── 📂 .venv/                       # Python virtual environment
```

---

## 📁 CẤU TRÚC THƯ MỤC DỰ KIẾN SAU NÂNG CẤP (V6.0)

```text
SOFT QUAN LY XE 6.0/
│
├── 📄 main.py                      # Entry point
├── 📄 requirements.txt             # Dependencies
├── 📄 README.md                    # Technical documentation
├── 📄 CHANGELOG.md                 # Lịch sử thay đổi
├── 📄 DEVELOPMENT_ROADMAP.md       # File này
├── 📄 .env.example                 # Template biến môi trường
├── 📄 .gitignore                   # Git ignore rules
│
│
├── 📂 app/                         # ⭐ MỚI: Core Application
│   ├── __init__.py
│   ├── main_window.py              # Main application window
│   ├── config.py                   # Cấu hình ứng dụng
│   ├── constants.py                # Hằng số
│   └── exceptions.py               # ⭐ MỚI: Custom exceptions
│
│
├── 📂 core/                        # ⭐ MỚI: Business Logic Layer
│   ├── __init__.py
│   ├── vehicle_service.py          # ⭐ MỚI: Business logic cho Vehicle
│   ├── dispatch_service.py         # ⭐ MỚI: Business logic cho Dispatch
│   ├── location_service.py         # ⭐ MỚI: Business logic cho Location
│   ├── report_service.py           # ⭐ MỚI: Business logic cho Reports
│   ├── backup_service.py           # ⭐ MỚI: Database backup/restore
│   ├── notification_service.py     # ⭐ MỚI: Alert & notifications
│   └── analytics_service.py        # ⭐ MỚI: Analytics & predictions
│
│
├── 📂 database/                    # Data Access Layer
│   ├── __init__.py
│   ├── connection.py               # ⭐ CẢI TIẾN: Connection pool
│   ├── base_repository.py          # ⭐ ĐỔI TÊN: base_manager → repository
│   ├── vehicle_repository.py       # ⭐ ĐỔI TÊN: vehicle_manager
│   ├── entity_repository.py        # ⭐ ĐỔI TÊN: entity_manager
│   ├── dispatch_repository.py      # ⭐ ĐỔI TÊN: dispatch_manager
│   ├── location_repository.py      # ⭐ ĐỔI TÊN: location_manager
│   ├── user_repository.py          # ⭐ MỚI: Quản lý user
│   ├── audit_repository.py         # ⭐ MỚI: Audit log
│   │
│   └── 📂 migrations/              # ⭐ MỚI: Database migrations
│       ├── __init__.py
│       ├── migration_manager.py    # Quản lý version schema
│       ├── v5_0_initial.py         # Schema V5.0
│       ├── v5_1_add_users.py       # Schema V5.1 - Thêm users
│       └── v6_0_analytics.py       # Schema V6.0 - Analytics tables
│
│
├── 📂 ui/                          # User Interface Layer
│   ├── __init__.py
│   │
│   ├── 📂 components/              # ⭐ MỚI: Tách thành sub-folder
│   │   ├── __init__.py
│   │   ├── toast.py                # Toast notification
│   │   ├── date_range_dialog.py    # Date picker dialog
│   │   ├── edit_vehicle_dialog.py  # Edit vehicle dialog
│   │   ├── location_swap_dialog.py # Swap location dialog
│   │   ├── treeview_styled.py      # ⭐ MỚI: Styled Treeview
│   │   └── loading_indicator.py    # ⭐ MỚI: Loading spinner
│   │
│   ├── 📂 tabs/                    # ⭐ MỚI: Tách tabs riêng
│   │   ├── __init__.py
│   │   ├── inbound_tab.py
│   │   ├── outbound_tab.py
│   │   ├── dispatch_tab.py
│   │   ├── stock_tab.py
│   │   ├── search_tab.py
│   │   ├── dashboard_tab.py
│   │   ├── log_tab.py
│   │   ├── yard_map_tab.py         # ⭐ MỚI: Bản đồ bãi xe 2D
│   │   └── analytics_tab.py        # ⭐ MỚI: Tab phân tích nâng cao
│   │
│   ├── 📂 dialogs/                 # ⭐ MỚI: Tách dialogs riêng
│   │   ├── __init__.py
│   │   ├── camera_scanner.py
│   │   ├── management_dialogs.py
│   │   ├── layout_management.py
│   │   ├── voucher_creation.py
│   │   ├── archive_explorer.py
│   │   ├── login_dialog.py         # ⭐ MỚI: Đăng nhập
│   │   ├── user_management.py      # ⭐ MỚI: Quản lý user
│   │   ├── backup_restore.py       # ⭐ MỚI: Backup/Restore dialog
│   │   └── settings_dialog.py      # ⭐ MỚI: Cài đặt nâng cao
│   │
│   ├── 📂 widgets/                 # ⭐ MỚI: Custom widgets
│   │   ├── __init__.py
│   │   ├── yard_canvas.py          # ⭐ MỚI: Canvas vẽ bãi xe
│   │   ├── vehicle_card.py         # ⭐ MỚI: Card hiển thị xe
│   │   ├── kpi_card.py             # ⭐ MỚI: Card KPI dashboard
│   │   └── search_bar.py           # ⭐ MỚI: Search với autocomplete
│   │
│   └── styles.py                   # ⭐ MỚI: Centralized styles/themes
│
│
├── 📂 utils/                       # ⭐ MỚI: Tách utilities riêng
│   ├── __init__.py
│   ├── helpers.py                  # General helpers
│   ├── validators.py               # ⭐ MỚI: Input validation (VIN, etc.)
│   ├── formatters.py               # ⭐ MỚI: Date/number formatters
│   ├── normalizers.py              # Data normalization (từ data_normalizer.py)
│   ├── logging_config.py           # ⭐ MỚI: Centralized logging
│   └── file_utils.py               # ⭐ MỚI: File operations
│
│
├── 📂 importers/                   # ⭐ MỚI: Tách import riêng
│   ├── __init__.py
│   ├── excel_importer.py           # Import xe từ Excel
│   ├── csv_importer.py             # ⭐ MỚI: Import từ CSV
│   └── json_importer.py            # ⭐ MỚI: Import từ JSON
│
│
├── 📂 exporters/                   # ⭐ ĐỔI TÊN: report_generators
│   ├── __init__.py
│   ├── excel_exporter.py           # Xuất Excel
│   ├── pdf_exporter.py             # Xuất PDF
│   ├── word_exporter.py            # Xuất Word
│   ├── csv_exporter.py             # ⭐ MỚI: Xuất CSV
│   └── json_exporter.py            # ⭐ MỚI: Xuất JSON
│
│
├── 📂 api/                         # ⭐ MỚI: REST API (Phase 3)
│   ├── __init__.py
│   ├── server.py                   # FastAPI/Flask server
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── vehicles.py             # /api/vehicles
│   │   ├── dispatches.py           # /api/dispatches
│   │   ├── locations.py            # /api/locations
│   │   ├── reports.py              # /api/reports
│   │   └── auth.py                 # /api/auth
│   ├── schemas/                    # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── vehicle_schema.py
│   │   └── dispatch_schema.py
│   └── middleware/
│       ├── __init__.py
│       └── auth_middleware.py      # JWT authentication
│
│
├── 📂 auth/                        # ⭐ MỚI: Authentication (Phase 1)
│   ├── __init__.py
│   ├── auth_manager.py             # Login/logout logic
│   ├── password_hasher.py          # Bcrypt hashing
│   ├── session_manager.py          # Session handling
│   └── permissions.py              # Role-based permissions
│
│
├── 📂 localization/                # ⭐ ĐỔI TÊN: từ translations.py
│   ├── __init__.py
│   ├── translation_manager.py      # Load/switch language
│   ├── vi.json                     # ⭐ MỚI: Tách ra JSON
│   ├── en.json
│   └── zh.json                     # ⭐ MỚI: Tiếng Trung (tùy chọn)
│
│
├── 📂 assets/                      # Static assets
│   ├── 📂 fonts/
│   │   ├── Arial.ttf
│   │   └── Arialbd.ttf
│   ├── 📂 images/
│   │   ├── logo.png
│   │   ├── logo_small.png
│   │   └── splash.png              # ⭐ MỚI: Splash screen
│   ├── 📂 icons/
│   │   ├── app_icon.ico
│   │   ├── inbound.png
│   │   ├── outbound.png
│   │   └── ... (các icon khác)
│   └── 📂 templates/
│       ├── voucher_template.docx   # Mẫu phiếu vận chuyển
│       └── report_template.docx    # ⭐ MỚI: Mẫu báo cáo
│
│
├── 📂 config/                      # Configuration
│   ├── config.ini                  # User settings
│   ├── owner_map.json              # Owner name mapping
│   ├── vehicle_types.json          # ⭐ MỚI: Danh sách loại xe
│   └── default_settings.json       # ⭐ MỚI: Default settings
│
│
├── 📂 data/                        # ⭐ MỚI: Data storage
│   ├── 📂 db/
│   │   └── vehicle_management.db   # SQLite database
│   ├── 📂 backups/                 # ⭐ MỚI: Backup files
│   │   ├── auto/                   # Auto backups
│   │   └── manual/                 # Manual backups
│   └── 📂 archives/                # Archived data
│
│
├── 📂 logs/                        # Log files
│   ├── app.log                     # Main application log
│   ├── error.log                   # ⭐ MỚI: Error-only log
│   └── audit.log                   # ⭐ MỚI: Audit trail log
│
│
├── 📂 tests/                       # ⭐ MỚI: Unit & Integration tests
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── 📂 unit/
│   │   ├── test_validators.py
│   │   ├── test_normalizers.py
│   │   ├── test_vehicle_service.py
│   │   └── test_dispatch_service.py
│   ├── 📂 integration/
│   │   ├── test_vehicle_repository.py
│   │   └── test_import_export.py
│   └── 📂 e2e/                     # End-to-end tests
│       └── test_workflows.py
│
│
├── 📂 docs/                        # ⭐ MỚI: Documentation
│   ├── user_guide.md               # Hướng dẫn sử dụng
│   ├── admin_guide.md              # ⭐ MỚI: Hướng dẫn quản trị
│   ├── api_reference.md            # ⭐ MỚI: API documentation
│   ├── database_schema.md          # ⭐ MỚI: DB schema docs
│   └── 📂 images/                  # Screenshots
│
│
└── 📂 scripts/                     # ⭐ MỚI: Utility scripts
    ├── build.py                    # Build executable
    ├── create_installer.py         # Create installer
    ├── db_migrate.py               # Run migrations
    └── generate_test_data.py       # Generate test data
```

---

## 📊 DATABASE SCHEMA DỰ KIẾN (V6.0)

### Các bảng hiện có (V5.0)

```sql
-- Bảng vehicles (Xe)
-- Bảng drivers (Tài xế)
-- Bảng transport_vehicles (Xe vận chuyển)
-- Bảng dispatches (Phiếu xuất)
-- Bảng locations (Vị trí bãi)
```

### Các bảng mới (V6.0)

```sql
-- ⭐ MỚI: Bảng users (Người dùng)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    email TEXT,
    role TEXT DEFAULT 'operator',  -- admin, operator, viewer
    is_active INTEGER DEFAULT 1,
    created_at TEXT,
    last_login TEXT
);

-- ⭐ MỚI: Bảng audit_logs (Nhật ký kiểm toán)
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,           -- CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    table_name TEXT,
    record_id TEXT,
    old_value TEXT,                 -- JSON
    new_value TEXT,                 -- JSON
    ip_address TEXT,
    created_at TEXT NOT NULL
);

-- ⭐ MỚI: Bảng backups (Lịch sử backup)
CREATE TABLE backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    size_bytes INTEGER,
    backup_type TEXT,               -- auto, manual, pre_archive
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL
);

-- ⭐ MỚI: Bảng notifications (Thông báo)
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    type TEXT,                      -- warning, info, alert
    title TEXT NOT NULL,
    message TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

-- ⭐ MỚI: Bảng settings (Cài đặt hệ thống)
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at TEXT
);

-- ⭐ MỚI: Bảng kpi_snapshots (Snapshot KPI hàng ngày)
CREATE TABLE kpi_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    total_in_stock INTEGER,
    total_dispatched INTEGER,
    avg_days_in_stock REAL,
    yard_utilization REAL,          -- Tỷ lệ lấp đầy
    created_at TEXT NOT NULL
);
```

---

## 🗓️ CHI TIẾT ROADMAP THEO PHASE

### 📌 PHASE 0 – Stabilization & Test Baseline (1-2 tuần)

**Mục tiêu:** Ổn định V5.x, khóa baseline để các phase sau có thể kiểm thử theo từng bước (ít rủi ro, dễ rollback).

| # | Hạng mục | Mô tả | Files cần tạo/sửa |
| --- | ------- | ----- | ----------------- |
| 0.1 | Logging chuẩn hóa | Chuẩn format log, thêm log level, tách log file theo ngày (nếu cần) | `utils.py`, `app_log.txt`/`logs/*` |
| 0.2 | Error handling tối thiểu | Thống nhất thông báo lỗi UI + ghi log, tránh crash im lặng | `ui/components.py`, `main.py` |
| 0.3 | Data integrity checks | Validate VIN/Owner/Date trước khi ghi DB, chặn dữ liệu rác | `data_normalizer.py`, `database/*` |
| 0.4 | Regression test baseline | Tạo bộ test tối thiểu cho DB layer + utilities (không cần UI) | `tests/*` (mới) |
| 0.5 | Release packaging checklist | Quy ước versioning, changelog, build/run checklist | `README.md`, `CHANGELOG.md` (mới nếu muốn) |

**Deliverables:**

- [ ] Bộ smoke test chạy được trên máy dev (import/compile + DB basic CRUD)
- [ ] Tài liệu “Regression suite” (danh sách ca test bắt buộc chạy trước khi release)
- [ ] Log có đủ thông tin để truy vết lỗi (thời gian, module, action, error)

**Acceptance Criteria (Tester):**

- [ ] Không có crash khi thao tác nhập/xuất/tồn cơ bản trên DB mẫu
- [ ] Log ghi lại được lỗi có stack trace khi phát sinh exception
- [ ] Validate dữ liệu đầu vào chặn được ít nhất: VIN rỗng/không hợp lệ, ngày sai format, owner rỗng

**Exit Gate (Go/No-Go):**

- [ ] Smoke + regression baseline pass 100%
- [ ] Không còn lỗi P0/P1 tồn đọng (P0: crash/data loss; P1: sai dữ liệu)

---

### ✅ PHASE 1A – Data Protection (Backup/Restore + Audit) ✅ HOÀN THÀNH

> **Hoàn thành:** 18/12/2025 | **Tag:** `v5.1.0-alpha` | **Tests:** 47 passed

| # | Tính năng | Mô tả | Files đã tạo/sửa | Status |
| --- | --------- | ----- | ----------------- | ------ |
| 1A.1 | Database Backup | Manual backup + export | `core/backup_service.py`, `ui/backup_dialog.py` | ✅ |
| 1A.2 | Restore & verify | Restore DB + verify integrity | `core/backup_service.py` | ✅ |
| 1A.3 | Audit Logging | Ghi log thay đổi dữ liệu (action/table/before/after) | `database/audit_repository.py` | ✅ |

**Deliverables:** ✅

- [x] Menu Backup/Restore trong Tools menu
- [x] Manual backup với timestamp và verify
- [x] Audit log ghi đầy đủ CRUD operations
- [x] Unit tests cho backup_service và audit_repository

**Exit Gate:** ✅ PASSED

- [x] Backup/Restore hoạt động chính xác
- [x] Audit log ghi đúng before/after values
- [x] 47 tests passed

---

### ✅ PHASE 1B – Soft Delete System ✅ HOÀN THÀNH

> **Hoàn thành:** 19/12/2025 | **Tag:** `v5.1.0-beta` | **Tests:** 113 passed (16 soft delete tests)

| # | Tính năng | Mô tả | Files đã tạo/sửa | Status |
| --- | --------- | ----- | ----------------- | ------ |
| 1B.1 | Soft Delete Schema | Thêm cột is_deleted, deleted_at, deleted_reason | `database/base_manager.py` | ✅ |
| 1B.2 | VehicleManager Methods | soft_delete, restore, hard_delete, list methods | `database/vehicle_manager.py` | ✅ |
| 1B.3 | Archive Explorer UI | Dialog quản lý xe đã xóa/lưu trữ | `ui/deleted_vehicles_dialog.py` | ✅ |

**Deliverables:** ✅

- [x] Soft delete thay vì xóa vĩnh viễn
- [x] UI quản lý xe đã xóa (restore/hard delete)
- [x] Tích hợp vào Tools menu
- [x] 16 unit tests cho soft delete

**Exit Gate:** ✅ PASSED

- [x] Soft delete không mất dữ liệu
- [x] Restore khôi phục đúng trạng thái
- [x] Hard delete yêu cầu lý do
- [x] 113 tests passed

---

### 📌 PHASE 1C – Security (Auth + RBAC) (2-4 tuần) – DEFERRED

> **Ghi chú:** Phase này được dời sang sau Phase 2 vì chưa có yêu cầu multi-user

| # | Tính năng | Mô tả | Files cần tạo/sửa |
| --- | --------- | ----- | ----------------- |
| 1C.1 | User Authentication | Login/logout, password hashing | `auth/*`, `database/user_repository.py` |
| 1C.2 | Role-based Access | Admin, Operator, Viewer; quyền theo action/tab | `auth/permissions.py`, `ui/*` |
| 1C.3 | Session & lock | Timeout/lock screen (tùy scope) | `auth/session.py` |
| 1C.4 | Audit Logging (security events) | Log đăng nhập, thất bại, đổi mật khẩu, phân quyền | `database/audit_repository.py` |

**Deliverables:**

- [ ] Login dialog khi khởi động app
- [ ] Quản lý user/role (tối thiểu: tạo user, reset mật khẩu)
- [ ] Chặn thao tác không đủ quyền (ẩn hoặc disable UI + thông báo)

**Exit Gate (Go/No-Go):**

- [ ] Test ma trận quyền (role x action) pass 100% theo bảng test
- [ ] Không có đường vòng UI/API cho phép bypass quyền

---

### 📌 PHASE 2 – Enhanced UX (1-2 tháng)

| # | Tính năng | Mô tả | Files cần tạo/sửa |
| --- | --------- | ----- | ----------------- |
| 2.1 | Advanced Search | Lọc theo ngày, trạng thái, block | `ui/tabs/search_tab.py` |
| 2.2 | Yard Map Visualization | Bản đồ 2D bãi xe | `ui/tabs/yard_map_tab.py`, `ui/widgets/yard_canvas.py` |
| 2.3 | Batch Operations | Chọn nhiều xe, thao tác hàng loạt | `ui/tabs/stock_tab.py` |
| 2.4 | Keyboard Shortcuts | Ctrl+N, Ctrl+F, F5, etc. | `app/main_window.py` |
| 2.5 | Auto-complete | Gợi ý VIN, Chủ hàng khi nhập | `ui/widgets/search_bar.py` |
| 2.6 | Notifications | Alert xe tồn lâu, bãi sắp đầy | `core/notification_service.py` |

**Deliverables:**

- [ ] Tab "Bản đồ bãi" với canvas tương tác
- [ ] Checkbox multi-select trong bảng Tồn kho
- [ ] Panel thông báo ở góc màn hình
- [ ] Phím tắt được hiển thị trong menu

**Acceptance Criteria (Tester):**

- [ ] Advanced search lọc đúng theo ngày/trạng thái/block và không sai kết quả so với DB
- [ ] Multi-select thao tác hàng loạt không làm sai số liệu tồn/xuất (không trùng thao tác, không thiếu)
- [ ] Keyboard shortcuts không xung đột với input field và có thể bật/tắt (nếu cần)
- [ ] Notifications không spam (cùng một cảnh báo không xuất hiện liên tục khi không đổi dữ liệu)

**Exit Gate (Go/No-Go):**

- [ ] Regression suite pass 100% và không phát sinh lỗi P0/P1
- [ ] UX mới không làm chậm đáng kể thao tác chính (nhập/xuất/tồn) trên DB mẫu

---

### 📌 PHASE 3 – API & Integration (2-3 tháng)

| # | Tính năng | Mô tả | Files cần tạo/sửa |
| --- | --------- | ----- | ----------------- |
| 3.1 | REST API Server | FastAPI backend | `api/*` |
| 3.2 | API Authentication | JWT tokens | `api/middleware/auth_middleware.py` |
| 3.3 | Webhook Events | Notify external systems | `api/webhooks.py` |
| 3.4 | Mobile API | Endpoints cho mobile app | `api/routes/mobile.py` |
| 3.5 | Export Formats | CSV, JSON export | `exporters/csv_exporter.py`, `exporters/json_exporter.py` |

**Deliverables:**

- [ ] API server chạy song song với Desktop app
- [ ] API documentation (Swagger UI)
- [ ] Webhook configuration UI
- [ ] API key management

**Acceptance Criteria (Tester):**

- [ ] API có auth (JWT/API key theo thiết kế) và endpoint không auth bị chặn đúng
- [ ] Swagger UI phản ánh đúng request/response và ví dụ chạy được với DB mẫu
- [ ] Webhook gửi đúng event, retry hợp lý, và không làm treo app khi endpoint ngoài bị lỗi
- [ ] API không cho phép bypass RBAC (nếu Phase 1B đã có) khi gọi trực tiếp endpoint

**Exit Gate (Go/No-Go):**

- [ ] Contract test (request/response) pass 100% cho các endpoint chính
- [ ] Security sanity check: không lộ dữ liệu nhạy cảm trong log/response

---

### 📌 PHASE 4 – Analytics & AI (3-6 tháng)

| # | Tính năng | Mô tả | Files cần tạo/sửa |
| --- | --------- | ----- | ----------------- |
| 4.1 | KPI Dashboard | Metrics, trends | `ui/tabs/analytics_tab.py`, `ui/widgets/kpi_card.py` |
| 4.2 | Trend Analysis | So sánh các kỳ | `core/analytics_service.py` |
| 4.3 | Predictions | Dự báo đơn giản | `core/prediction_service.py` |
| 4.4 | Custom Reports | Report builder | `ui/dialogs/report_builder.py` |
| 4.5 | Data Export Scheduling | Auto export định kỳ | `core/scheduler_service.py` |

**Deliverables:**

- [ ] Tab Analytics với các KPI cards
- [ ] Biểu đồ trend so sánh
- [ ] Cảnh báo dự báo (xe sắp tồn quá hạn)
- [ ] Scheduled report via email

**Acceptance Criteria (Tester):**

- [ ] KPI tính đúng theo định nghĩa (có tài liệu công thức) khi đối chiếu với dữ liệu DB mẫu
- [ ] Trend chart hiển thị đúng khoảng thời gian và không sai lệch số liệu khi đổi filter
- [ ] Cảnh báo dự báo có ngưỡng rõ ràng, có thể bật/tắt, và không gây false positive quá mức
- [ ] Scheduled report gửi đúng lịch, đúng người nhận, và có log/audit cho lần gửi

**Exit Gate (Go/No-Go):**

- [ ] Analytics pass 100% theo bộ test số liệu (golden dataset)
- [ ] Không ảnh hưởng hiệu năng thao tác nghiệp vụ cốt lõi (nhập/xuất/tồn)

---

## 🧪 TEST PLAN & RELEASE GATES (Dành cho Dev + Tester)

### Test Baseline (áp dụng cho mọi phase)

**Test Data chuẩn:**

- 01 DB trống (fresh)
- 01 DB mẫu nhỏ (50-200 xe) có đủ trạng thái (inbound, in_stock, dispatched, archived)
- 01 DB “edge cases”: VIN trùng, owner có dấu/không dấu, ngày rỗng/sai format, ký tự đặc biệt

**Smoke suite (bắt buộc chạy mỗi lần build):**

- App khởi động được, load config, không crash
- CRUD tối thiểu: thêm xe → xem tồn → xuất xe → tra cứu
- Import/Export tối thiểu (nếu phase có ảnh hưởng): import 1 file mẫu + export 1 báo cáo

**Regression suite (bắt buộc trước khi merge/release):**

- Nhập bãi: validate VIN/Owner/Date, không tạo bản ghi rác
- Xuất bãi: xuất lẻ + xuất nhiều (dispatch), không sai số lượng
- Tồn bãi: lọc/tra cứu cơ bản, cập nhật vị trí (nếu có)
- Archive: lưu trữ/tra cứu dữ liệu lưu trữ (nếu feature hiện có)

### Release Gates (Go/No-Go)

**Gate 0 (trước khi bắt đầu Phase 0):**

- Có baseline tag/version + backup source + backup DB mẫu
- Có danh sách ca test smoke/regression + người chịu trách nhiệm chạy

**Gate 1 (kết thúc Phase 0):**

- Smoke + regression baseline pass 100%
- Không còn lỗi P0/P1 tồn đọng

**Gate 1A (kết thúc Phase 1A - Backup/Restore):**

- Test backup/restore/rollback pass 100% trên cả DB nhỏ và DB lớn (tùy thực tế)
- Restore sai file không làm mất DB hiện tại

**Gate 1B (kết thúc Phase 1B - Auth/RBAC):**

- Ma trận quyền (role x action) pass 100%
- Password hash + không có bypass quyền qua UI

**Gate 2+ (kết thúc Phase 2/3/4):**

- Regression pass 100% + không phát sinh P0/P1
- Nếu có thay đổi schema/migration: có script + test migrate + test rollback (nếu áp dụng)

---

## 🔧 TECHNICAL SPECIFICATIONS

### Dependencies mới cần thêm

```txt
# requirements.txt - V6.0

# === Existing ===
customtkinter
tkcalendar
pandas
openpyxl
matplotlib==3.8.1
seaborn==0.13.0
reportlab
qrcode[pil]
python-docx
docxtpl
unidecode
opencv-python
thefuzz
python-Levenshtein

# === Phase 1 – Security ===
bcrypt>=4.0.0                 # Password hashing
cryptography>=41.0.0          # Encryption

# === Phase 2 – UX ===
pillow>=10.0.0                # Image processing (đã có qua qrcode)

# === Phase 3 – API ===
fastapi>=0.104.0              # REST API framework
uvicorn>=0.24.0               # ASGI server
pydantic>=2.5.0               # Data validation
python-jose>=3.3.0            # JWT tokens
httpx>=0.25.0                 # HTTP client

# === Phase 4 – Analytics ===
numpy>=1.26.0                 # Numerical computing
scikit-learn>=1.3.0           # Simple ML predictions (optional)

# === Development ===
pytest>=7.4.0                 # Testing
pytest-cov>=4.1.0             # Coverage
black>=23.0.0                 # Code formatting
flake8>=6.1.0                 # Linting
```

### Coding Standards

```python
# Type hints bắt buộc cho tất cả functions mới
def add_vehicle(
    self, 
    vin: str, 
    owner: str, 
    vehicle_type: str,
    date_in: datetime,
    location_id: int
) -> dict[str, Any]:
    """
    Thêm một xe mới vào CSDL.
    
    Args:
        vin: Số khung xe (17 ký tự)
        owner: Tên chủ hàng
        vehicle_type: Loại xe
        date_in: Ngày nhập bãi
        location_id: ID vị trí trong bãi
    
    Returns:
        dict: {"success": bool, "message": str, "data": Optional[dict]}
    
    Raises:
        ValidationError: Nếu VIN không hợp lệ
        DatabaseError: Nếu có lỗi CSDL
    """
    pass
```

### File Naming Conventions

- **Classes**: `PascalCase` (VehicleManager, InboundTab)
- **Functions/Methods**: `snake_case` (add_vehicle, get_in_stock)
- **Files**: `snake_case.py` (vehicle_manager.py, inbound_tab.py)
- **Constants**: `UPPER_SNAKE_CASE` (STATUS_IN_STOCK, DB_FILE)

---

## ✅ CHECKLIST TRƯỚC KHI BẮT ĐẦU PHASE 0

- [ ] Backup toàn bộ source code hiện tại
- [ ] Backup DB mẫu/DB thật (nếu có) và xác nhận có thể restore
- [ ] Tạo tag baseline (ví dụ: `v5.0-baseline`) + ghi rõ môi trường chạy (Python version)
- [ ] Tạo branch làm việc cho Phase 0 (ví dụ: `feature/phase-0-stabilization`)
- [ ] Chuẩn hóa bộ test data (fresh DB / DB mẫu / edge cases)
- [ ] Setup pytest (ưu tiên test cho DB layer + utils; chưa cần UI automation)
- [ ] Định nghĩa smoke suite + regression suite (danh sách case + expected results)
- [ ] Quy ước mức độ bug (P0/P1/P2) + quy trình xử lý/rollback
- [ ] Cập nhật requirements.txt (nếu Phase 0 có thay đổi phụ thuộc)

---

## 📞 LIÊN HỆ & GHI CHÚ

**Developed by:** Tiền - Cảng Tân Thuận

**Ghi chú:**

- Tài liệu này sẽ được cập nhật theo tiến độ phát triển
- Mỗi Phase hoàn thành cần cập nhật CHANGELOG.md
- Version numbering: MAJOR.MINOR.PATCH (V5.0.0 → V5.1.0 → V6.0.0)

---

Cập nhật lần cuối: 19/12/2025
