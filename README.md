# 🚗 Vehicle Management System - V1.0 @2026

> **Phần mềm Quản lý Xe** - Ứng dụng desktop quản lý xe nhập/xuất bãi cho doanh nghiệp vận tải và logistics.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

## 📋 Mục lục

- [Giới thiệu](#-giới-thiệu)
- [Tính năng](#-tính-năng)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt](#-cài-đặt)
- [Sử dụng](#-sử-dụng)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Testing](#-testing)
- [Đóng góp](#-đóng-góp)
- [Tác giả](#-tác-giả)
- [License](#-license)

---

## 🎯 Giới thiệu

**Vehicle Management System** là ứng dụng desktop được phát triển bằng Python và CustomTkinter, hỗ trợ quản lý xe theo quy trình:

```
Nhập bãi → Tạo phiếu điều xe → Xuất bãi → Báo cáo/Thống kê
```

Phù hợp cho:
- Bãi xe cảng biển, cảng container
- Công ty vận tải, logistics
- Đại lý ô tô, showroom
- Bãi giữ xe tập trung

---

## ✨ Tính năng

### Nghiệp vụ cốt lõi
| Tính năng | Mô tả |
|-----------|-------|
| **Nhập bãi** | Nhập thủ công hoặc import Excel hàng loạt |
| **Tạo phiếu điều xe** | Gom nhiều xe vào 1 phiếu, in phiếu Word/PDF |
| **Xuất bãi** | Xuất theo phiếu hoặc xuất lẻ từng xe |
| **Tồn kho** | Quản lý xe trong bãi, chỉnh sửa, xóa mềm |
| **Bản đồ bãi** | Xem trực quan vị trí xe, slot trống/đầy |
| **Tra cứu** | Tìm kiếm nâng cao theo nhiều tiêu chí |

### Quản trị hệ thống
| Tính năng | Mô tả |
|-----------|-------|
| **Đăng nhập** | 3 vai trò (Admin/Supervisor/Operator) với 25+ quyền |
| **Audit Log** | Ghi lại mọi thao tác CRUD, đăng nhập/đăng xuất |
| **Backup/Restore** | Sao lưu và phục hồi dữ liệu có mã hóa |
| **Đa ngôn ngữ** | Tiếng Việt / English |

### Báo cáo & Thống kê
| Tính năng | Mô tả |
|-----------|-------|
| **Dashboard** | Biểu đồ thống kê nhập/xuất/tồn |
| **Xuất báo cáo** | Excel, PDF, Word với biểu đồ |
| **Tổng hợp nhiều bãi** | Import dữ liệu từ các bãi, khử trùng tự động |

### Tiện ích
- ⌨️ **Phím tắt**: F5, Ctrl+N/F/E/D/M/B/Q
- 🔔 **Thông báo**: Xe tồn lâu, bãi sắp đầy
- 🎯 **Auto-complete**: Gợi ý VIN, Chủ hàng khi nhập
- 📷 **Quét mã vạch**: Hỗ trợ camera/scanner

---

## 💻 Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|------------|---------|
| **OS** | Windows 10/11 |
| **Python** | 3.11+ (nếu chạy từ source) |
| **RAM** | 4GB trở lên |
| **Disk** | 500MB trống |

---

## 🚀 Cài đặt

### Cách 1: Chạy từ source (Developer)

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/vehicle-management-system.git
cd vehicle-management-system

# Tạo virtual environment
python -m venv .venv
.venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng
python main.py
```

### Cách 2: Chạy file .exe (End User)

1. Tải file `VehicleManagement_V1.0.exe` từ [Releases](../../releases)
2. Giải nén và chạy file .exe
3. Đăng nhập với tài khoản mặc định: `admin` / `admin123`

---

## 📖 Sử dụng

### Đăng nhập
- **Admin**: Toàn quyền quản trị
- **Supervisor**: Quản lý nghiệp vụ, xem báo cáo
- **Operator**: Nhập/xuất xe cơ bản

### Quy trình cơ bản
1. **Nhập bãi**: Tab "Nhập bãi" → Điền thông tin hoặc Import Excel
2. **Tạo phiếu**: Tab "Điều xe" → Chọn xe → Tạo phiếu
3. **Xuất bãi**: Tab "Xuất bãi" → Chọn phiếu → Xác nhận xuất
4. **Báo cáo**: Tab "Dashboard" → Xem thống kê

> 📚 Xem chi tiết tại [User_Guide.md](User_Guide.md)

---

## 📁 Cấu trúc dự án

```
vehicle-management-system/
├── main.py                 # Entry point
├── config.py               # Cấu hình ứng dụng
├── translations.py         # Đa ngôn ngữ (i18n)
├── auth/                   # Xác thực & phân quyền
├── database/               # Quản lý CSDL SQLite
├── ui/                     # Giao diện (CustomTkinter)
├── core/                   # Logic nghiệp vụ
├── report_generators/      # Xuất báo cáo Excel/PDF/Word
├── reporting/              # Tổng hợp nhiều bãi
├── tools/                  # Script tiện ích CLI
├── tests/                  # Unit & Integration tests
├── assets/                 # Font, logo, file mẫu
└── logs/                   # Log runtime
```

---

## 🧪 Testing

```bash
# Chạy toàn bộ test
python -m pytest

# Chạy với chi tiết
python -m pytest -v

# Chạy test cụ thể
python -m pytest tests/unit/test_auth.py -v

# Xem coverage
python -m pytest --cov=. --cov-report=html
```

---

## 🤝 Đóng góp

1. Fork repository
2. Tạo branch: `git checkout -b feature/TenTinhNang`
3. Commit: `git commit -m "Add: Mô tả thay đổi"`
4. Push: `git push origin feature/TenTinhNang`
5. Tạo Pull Request

---

## 👨‍💻 Tác giả

**Tiền - Cảng Tân Thuận**

---

## 📄 License

MIT License - Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---

<p align="center">
  Made with ❤️ in Vietnam 🇻🇳
</p>
