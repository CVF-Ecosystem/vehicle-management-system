# 🚗 Vehicle Management System — v1.0
<!-- version header should match `config.APP_VERSION_DISPLAY`; update there and re‑generate docs if needed -->

> **Phần mềm Quản lý Xe** — Ứng dụng desktop quản lý xe nhập/xuất bãi cho doanh nghiệp vận tải và logistics.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)](https://www.microsoft.com/windows)
[![CI](https://github.com/Blackbird081/vehicle-management-system/actions/workflows/ci.yml/badge.svg)](https://github.com/Blackbird081/vehicle-management-system/actions/workflows/ci.yml)
[![Code Quality](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## 📋 Mục lục

- [Giới thiệu](#-giới-thiệu)
- [Tính năng](#-tính-năng)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt](#-cài-đặt)
- [Sử dụng](#-sử-dụng)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Bảo mật](#-bảo-mật)
- [Testing](#-testing)
- [Đóng góp](#-đóng-góp)
- [Changelog](#-changelog)
- [License](#-license)

---

## 🎯 Giới thiệu

**Vehicle Management System** là ứng dụng desktop được phát triển bằng Python và CustomTkinter, hỗ trợ quản lý xe theo quy trình:

```
Nhập bãi → Tạo phiếu điều xe → Xuất bãi → Báo cáo/Thống kê
```

Phù hợp cho:
- 🚢 Bãi xe cảng biển, cảng container
- 🚛 Công ty vận tải, logistics
- 🏪 Đại lý ô tô, showroom
- 🅿️ Bãi giữ xe tập trung

---

## ✨ Tính năng

### Nghiệp vụ cốt lõi
| Tính năng | Mô tả |
|-----------|-------|
| **Nhập bãi** | Nhập thủ công hoặc import Excel hàng loạt với fuzzy matching tên chủ hàng |
| **Tạo phiếu điều xe** | Gom nhiều xe vào 1 phiếu, in phiếu Word/PDF |
| **Xuất bãi** | Xuất theo phiếu hoặc xuất lẻ từng xe |
| **Tồn kho** | Quản lý xe trong bãi, chỉnh sửa, xóa mềm (soft delete) |
| **Bản đồ bãi** | Xem trực quan vị trí xe, slot trống/đầy, zoom và filter |
| **Tra cứu** | Tìm kiếm nâng cao theo VIN, chủ hàng, loại xe, ngày |

### Quản trị hệ thống
| Tính năng | Mô tả |
|-----------|-------|
| **Đăng nhập** | 3 vai trò (Admin/Operator/Viewer) với 25+ quyền chi tiết |
| **Rate Limiting** | Giới hạn 10 lần thử đăng nhập/60 giây để chống brute force |
| **Session Timeout** | Tự động đăng xuất sau 30 phút không hoạt động |
| **Audit Log** | Ghi lại mọi thao tác CRUD, đăng nhập/đăng xuất |
| **Backup/Restore** | Sao lưu và phục hồi dữ liệu với kiểm tra tính toàn vẹn |
| **Đa ngôn ngữ** | Tiếng Việt / English |

### Báo cáo & Thống kê
| Tính năng | Mô tả |
|-----------|-------|
| **Dashboard** | Biểu đồ thống kê nhập/xuất/tồn theo thời gian |
| **Web Dashboard** | Streamlit dashboard tương tác (chạy song song) |
| **Xuất báo cáo** | Excel, PDF, Word với biểu đồ và định dạng chuyên nghiệp |
| **Tổng hợp nhiều bãi** | Import bundle từ các bãi, khử trùng tự động, báo cáo HQ |

### Tiện ích
- ⌨️ **Phím tắt**: F5 (refresh), Ctrl+N/F/E/D/M/B/Q
- 🔔 **Thông báo**: Xe tồn lâu, bãi sắp đầy
- 🎯 **Auto-complete**: Gợi ý VIN, Chủ hàng khi nhập
- 📷 **Quét mã vạch**: Hỗ trợ camera/scanner
- 🔄 **Auto-update**: Tự động kiểm tra phiên bản mới từ GitHub

---

## 💻 Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|------------|---------|
| **OS** | Windows 10/11 hoặc Linux (Ubuntu 20.04+) |
| **Python** | 3.11+ (nếu chạy từ source) |
| **RAM** | 4GB trở lên |
| **Disk** | 500MB trống |
| **Network** | Không bắt buộc (offline-first) |

---

## 🚀 Cài đặt

### Cách 1: Chạy từ source (Developer)

```bash
# Clone repository
git clone https://github.com/Blackbird081/vehicle-management-system.git
cd vehicle-management-system

# Tạo virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng
python main.py
```

### Cách 2: Chạy file .exe (End User — Windows)

1. Tải file `VehicleManagement_v1.0.exe` từ [Releases](../../releases)
2. Giải nén và chạy file .exe
3. Đăng nhập với tài khoản mặc định: `admin` / `admin123`
4. **⚠️ Đổi mật khẩu admin ngay sau lần đăng nhập đầu tiên!**

### Cài đặt pre-commit hooks (Developer)

```bash
pip install pre-commit
pre-commit install
```

---

## 📖 Sử dụng

### Đăng nhập
| Vai trò | Quyền |
|---------|-------|
| **Admin** | Toàn quyền: quản lý user, xem audit log, backup/restore |
| **Operator** | Nhập/xuất xe, tạo phiếu, xem báo cáo |
| **Viewer** | Chỉ xem, không thể thay đổi dữ liệu |

### Quy trình cơ bản
1. **Nhập bãi**: Tab "Nhập bãi" → Điền thông tin hoặc Import Excel
2. **Tạo phiếu**: Tab "Điều xe" → Chọn xe → Tạo phiếu
3. **Xuất bãi**: Tab "Xuất bãi" → Chọn phiếu → Xác nhận xuất
4. **Báo cáo**: Tab "Dashboard" → Xem thống kê

> 📚 Xem chi tiết tại [User_Guide.md](User_Guide.md)

### Reset mật khẩu Admin

Nếu quên mật khẩu admin, dùng CLI tool (yêu cầu quyền truy cập file system):

```bash
python tools/reset_admin.py
# Hoặc
python tools/reset_admin.py --password <new_password>
python tools/reset_admin.py --unlock-only  # Chỉ mở khóa tài khoản
```

---

## 📁 Cấu trúc dự án

```
vehicle-management-system/
├── main.py                     # Entry point
├── config.py                   # Cấu hình ứng dụng (SemVer, paths, constants)
├── translations.py             # Đa ngôn ngữ (i18n) — vi/en
├── ruff.toml                   # Cấu hình linter
├── .pre-commit-config.yaml     # Pre-commit hooks
│
├── auth/                       # Xác thực & phân quyền
│   ├── auth_manager.py         # Session management, rate limiting
│   └── permissions.py          # RBAC permission system
│
├── database/                   # Quản lý CSDL SQLite
│   ├── base_manager.py         # Singleton connection, schema migration
│   ├── vehicle_manager.py      # CRUD xe, validation, audit hooks
│   ├── dispatch_manager.py     # Quản lý phiếu xuất
│   ├── user_repository.py      # User auth, rate limiting, bcrypt
│   └── audit_repository.py     # Audit log repository
│
├── ui/                         # Giao diện (CustomTkinter)
│   ├── inbound_tab.py          # Tab nhập bãi
│   ├── stock_tab.py            # Tab tồn kho
│   ├── dispatch_tab.py         # Tab điều xe
│   ├── outbound_tab.py         # Tab xuất lẻ
│   ├── yard_map_tab.py         # Bản đồ bãi
│   ├── dashboard_tab.py        # Dashboard thống kê
│   ├── web_dashboard_manager.py # Quản lý Streamlit dashboard
│   └── virtual_treeview.py     # PaginatedTreeview cho dataset lớn
│
├── core/                       # Logic nghiệp vụ
│   ├── backup_service.py       # Backup/restore với integrity check
│   ├── notification_service.py # Thông báo xe tồn lâu, bãi đầy
│   └── update_checker.py       # Auto-update từ GitHub Releases
│
├── report_generators/          # Xuất báo cáo
│   ├── excel_generator.py      # Excel với biểu đồ
│   ├── pdf_generator.py        # PDF với font tiếng Việt
│   └── word_generator.py       # Word template
│
├── reporting/                  # Tổng hợp nhiều bãi (HQ)
│   ├── central_report.py       # Báo cáo tổng hợp
│   ├── central_store.py        # Import bundle từ bãi
│   └── transfer_normalizer.py  # Phát hiện chuyển bãi
│
├── tools/                      # Script tiện ích CLI
│   ├── reset_admin.py          # Reset mật khẩu admin an toàn
│   ├── export_site_bundle.py   # Xuất bundle từ bãi
│   ├── import_bundles.py       # Import bundle vào HQ
│   ├── generate_central_report.py # Tạo báo cáo HQ
│   └── export_translations_json.py # Xuất translations sang JSON
│
├── tests/                      # Tests
│   ├── conftest.py             # Fixtures, DB isolation
│   ├── test_smoke.py           # Smoke tests
│   ├── test_logic_pytest.py    # Logic tests (pytest chuẩn)
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
│
└── assets/                     # Font, logo
```

---

## 🔒 Bảo mật

### Tính năng bảo mật
- **Bcrypt password hashing** — Mật khẩu được hash với bcrypt (không lưu plaintext)
- **Rate limiting** — Giới hạn 10 lần thử đăng nhập/60 giây per username
- **Account lockout** — Khóa tài khoản sau 5 lần sai mật khẩu (15 phút)
- **Session timeout** — Tự động đăng xuất sau 30 phút không hoạt động
- **SQL injection prevention** — Whitelist table/column names + parameterized queries
- **Audit trail** — Ghi lại mọi thao tác với timestamp và user info
- **Separate security DB** — DB bảo mật tách biệt khỏi DB xe

### Lưu ý bảo mật
> ⚠️ **Đổi mật khẩu admin mặc định (`admin123`) ngay sau khi cài đặt!**

> ⚠️ **Không chia sẻ file `config/security.db` — chứa thông tin đăng nhập đã hash**

---

## 🧪 Testing

```bash
# Chạy toàn bộ test
python -m pytest

# Chạy với chi tiết
python -m pytest -v

# Chạy smoke tests nhanh
python -m pytest -m smoke

# Chạy với coverage report
python -m pytest --cov=. --cov-report=html --cov-omit="tests/*,tao_phieu_v1.2.py"

# Chạy test logic cụ thể
python -m pytest tests/test_logic_pytest.py -v
```

### CI/CD
Mỗi push/PR tự động chạy:
1. **Lint** — ruff linter + formatter check
2. **Tests** — pytest trên Python 3.11 và 3.12 với coverage
3. **Security** — bandit security scan + safety dependency check

---

## 🤝 Đóng góp

1. Fork repository
2. Tạo branch: `git checkout -b feature/TenTinhNang`
3. Cài pre-commit: `pre-commit install`
4. Commit theo [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: Thêm tính năng mới
   fix: Sửa lỗi
   docs: Cập nhật tài liệu
   refactor: Tái cấu trúc code
   test: Thêm/sửa test
   ```
5. Push: `git push origin feature/TenTinhNang`
6. Tạo Pull Request

### Coding Standards
- Python 3.11+, type hints cho public functions
- Docstrings theo Google style
- Chạy `ruff check .` trước khi commit
- Test coverage ≥ 70% cho code mới

---

## 📝 Changelog

### v1.0.0 (2026-02-27)
**Security:**
- 🔒 Xóa cơ chế `unlock.txt` backdoor nguy hiểm
- 🔒 Thêm rate limiting cho login (10 lần/60 giây)
- 🔒 Thêm `threading.Lock()` cho write operations trong user_repository

**Code Quality:**
- ✅ Fix 18 bare `except:` → specific exceptions
- ✅ Xóa dead code và duplicate method trong auth_manager
- ✅ Xóa 8 debug `print()` trong pdf_generator
- ✅ Chuyển tất cả inline imports lên đầu file
- ✅ `APP_VERSION` theo SemVer (`1.0.0`)
- ✅ Thêm type hints cho utils.py

**Architecture:**
- 🏗️ Tách `WebDashboardManager` ra `ui/web_dashboard_manager.py`
- 🏗️ Thêm `ui/virtual_treeview.py` — PaginatedTreeview cho dataset lớn

**Performance:**
- ⚡ `on_data_changed()` chỉ refresh tab đang active
- ⚡ Thay `time.sleep(3)` bằng polling loop khi chờ Streamlit

**New Features:**
- 🆕 `core/update_checker.py` — Auto-update từ GitHub Releases
- 🆕 `tools/reset_admin.py` — CLI tool reset admin an toàn
- 🆕 `tools/export_translations_json.py` — Export translations sang JSON
- 🆕 GitHub Actions CI với lint + tests + security scan
- 🆕 Pre-commit hooks với ruff

**Testing:**
- 🧪 `tests/test_logic_pytest.py` — pytest chuẩn với 25+ test cases
- 🧪 Fix test data status constants (`IN_STOCK`, `SHIPPED`)

---

## 👨‍💻 Tác giả

**Tiền — Cảng Tân Thuận**

---

## 📄 License

MIT License — Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---

<p align="center">
  Made with ❤️ in Vietnam 🇻🇳
</p>
