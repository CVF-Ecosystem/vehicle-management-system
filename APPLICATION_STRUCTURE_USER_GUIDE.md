# 📘 Hướng Dẫn Cấu Trúc Ứng Dụng - Dành Cho Người Dùng Cuối

## Mục Lục
1. [Tổng Quan Ứng Dụng](#tổng-quan-ứng-dụng)
2. [Cấu Trúc Thư Mục](#cấu-trúc-thư-mục)
3. [Giải Thích Chi Tiết Từng File](#giải-thích-chi-tiết-từng-file)
4. [Các Tệp Cấu Hình](#các-tệp-cấu-hình)
5. [Cách Thức Hoạt Động](#cách-thức-hoạt-động)

---

## 🎯 Tổng Quan Ứng Dụng

**SOFT QUẢN LÝ XE V5.1.0** là một hệ thống quản lý kho xe toàn diện, cho phép:

- ✅ Quản lý thông tin xe (nhập xe, xuất xe, theo dõi trạng thái)
- ✅ Quản lý vận chuyển (tạo phiếu vận chuyển, theo dõi lô xe)
- ✅ Quản lý người dùng (phân quyền, kiểm soát truy cập)
- ✅ Quản lý sao lưu dữ liệu (tạo bản sao, khôi phục)
- ✅ Theo dõi lịch sử thay đổi (audit log)
- ✅ Tạo báo cáo (Excel, PDF, Word)

---

## 📂 Cấu Trúc Thư Mục

```
SOFT QUAN LY XE 5.0 - new/
│
├── 🚀 CHƯƠNG TRÌNH CHÍNH
│   ├── main.py                      ← Khởi động ứng dụng
│   ├── config.py                    ← Cấu hình chung
│   ├── exceptions.py                ← Định nghĩa lỗi
│   └── utils.py                     ← Hàm tiện ích
│
├── 📦 QUẢN LÝ XE (database/)
│   ├── vehicle_manager.py           ← Quản lý thông tin xe
│   ├── dispatch_manager.py          ← Quản lý vận chuyển
│   ├── entity_manager.py            ← Quản lý thực thể chung
│   ├── location_manager.py          ← Quản lý địa điểm
│   ├── user_repository.py           ← Quản lý tài khoản người dùng
│   ├── audit_repository.py          ← Theo dõi lịch sử thay đổi
│   ├── base_manager.py              ← Kết nối cơ sở dữ liệu
│   └── __init__.py                  ← Module database
│
├── 🔐 XÁC THỰC & PHÂN QUYỀN (auth/)
│   ├── auth_manager.py              ← Quản lý phiên đăng nhập
│   ├── permissions.py               ← Định nghĩa quyền hạn
│   └── __init__.py                  ← Module auth
│
├── ⚙️ CÁC DỊCH VỤ BACKEND (core/)
│   ├── backup_service.py            ← Sao lưu & khôi phục dữ liệu
│   ├── notification_service.py      ← Gửi thông báo
│   └── __init__.py                  ← Module core
│
├── 🎨 GIAO DIỆN NGƯỜI DÙNG (ui/)
│   ├── login_dialog.py              ← Cửa sổ đăng nhập
│   ├── dashboard_tab.py             ← Trang chủ
│   ├── stock_tab.py                 ← Quản lý kho
│   ├── inbound_tab.py               ← Nhập xe
│   ├── outbound_tab.py              ← Xuất xe
│   ├── dispatch_tab.py              ← Quản lý vận chuyển
│   ├── yard_map_tab.py              ← Bản đồ bãi
│   ├── search_tab.py                ← Tìm kiếm nâng cao
│   ├── log_tab.py                   ← Xem lịch sử
│   ├── archive_explorer_dialog.py   ← Duyệt kho lưu trữ
│   ├── user_management_dialog.py    ← Quản lý người dùng
│   ├── voucher_creation_dialog.py   ← Tạo phiếu
│   ├── components.py                ← Các thành phần UI
│   ├── layout_manager.py            ← Quản lý bố cục
│   └── __init__.py                  ← Module ui
│
├── 📊 CÔNG CỤ BÁO CÁO (report_generators/)
│   ├── excel_generator.py           ← Tạo báo cáo Excel
│   ├── pdf_generator.py             ← Tạo báo cáo PDF
│   ├── word_generator.py            ← Tạo báo cáo Word
│   └── central_excel_report.py      ← Báo cáo tập trung
│
├── 📈 QUẢN LÝ BÁO CÁO (reporting/)
│   ├── central_report.py            ← Tạo báo cáo toàn hệ thống
│   ├── central_event_store.py       ← Lưu trữ sự kiện
│   ├── central_transfer_report.py   ← Báo cáo vận chuyển
│   ├── site_bundle.py               ← Gói dữ liệu chi nhánh
│   └── __init__.py                  ← Module reporting
│
├── 🛠️ CÔNG CỤ TIỆN ÍCH (tools/)
│   ├── generate_central_report.py   ← Lệnh tạo báo cáo
│   ├── generate_transfer_report.py  ← Lệnh tạo báo cáo vận chuyển
│   ├── import_bundles.py            ← Nhập dữ liệu từ chi nhánh
│   └── export_site_bundle.py        ← Xuất dữ liệu chi nhánh
│
├── 🧪 KIỂM THỬ (tests/)
│   ├── conftest.py                  ← Cấu hình pytest
│   ├── test_smoke.py                ← Kiểm thử cơ bản
│   └── unit/, integration/          ← Kiểm thử chi tiết
│
├── ⚙️ CẤU HÌNH & DỮ LIỆU
│   ├── config.ini                   ← Thiết lập chung
│   ├── config/config.ini            ← Cấu hình thêm
│   ├── owner_map.json               ← Ánh xạ chủ xe
│   └── pytest.ini                   ← Cấu hình kiểm thử
│
├── 📝 TÀI LIỆU & XỬ LÝ DỮ LIỆU
│   ├── data_normalizer.py           ← Kiểm tra & chuẩn hóa dữ liệu
│   ├── excel_importer.py            ← Nhập dữ liệu từ Excel
│   ├── api_client.py                ← Kết nối API bên ngoài
│   ├── translations.py              ← Dịch ngôn ngữ
│   ├── check_translations.py        ← Kiểm tra bản dịch
│   ├── voucher_generator.py         ← Tạo phiếu vận chuyển
│   ├── tao_phieu_v1.2.py            ← Tạo phiếu (phiên bản cũ)
│   └── layout_management_dialog.py  ← Quản lý bố cục
│
├── 📚 TÀI LIỆU & LỒI
│   ├── README.md                    ← Giới thiệu ứng dụng
│   ├── User_Guide.md                ← Hướng dẫn người dùng
│   ├── ROADMAP.md                   ← Kế hoạch phát triển
│   ├── app_log.txt                  ← Nhật ký ứng dụng
│   └── main.spec                    ← Cấu hình biên dịch
│
└── 📁 CÁC THƯ MỤC KHÁC
    ├── logs/                        ← Lưu các tệp nhật ký
    ├── assets/                      ← Hình ảnh, biểu tượng
    ├── icons/                       ← Biểu tượng ứng dụng
    ├── archives/                    ← Kho lưu trữ dữ liệu cũ
    └── __pycache__/                 ← Tệp cache Python (tự động)
```

---

## 📖 Giải Thích Chi Tiết Từng File

### 🚀 CHƯƠNG TRÌNH CHÍNH

#### **main.py** - Khởi Động Ứng Dụng
**Chức năng:**
- Điểm khởi động của toàn bộ ứng dụng
- Tạo giao diện người dùng (UI)
- Nạp tất cả các module khác
- Quản lý các cửa sổ ứng dụng

**Logic hoạt động:**
1. Khởi động ứng dụng khi người dùng chạy `main.py`
2. Kiểm tra thông tin đăng nhập (gọi `LoginDialog`)
3. Nếu đăng nhập thành công → hiển thị giao diện chính
4. Nếu đăng nhập thất bại → lặp lại bước 2
5. Khi đóng giao diện → kết thúc ứng dụng

**Không cần chỉnh sửa:** Người dùng cuối bỏ qua file này

---

#### **config.py** - Cấu Hình Chung
**Chức năng:**
- Lưu trữ các hằng số của ứng dụng (kích thước, màu sắc, v.v.)
- Cấu hình thông số kỹ thuật

**Ví dụ cấu hình:**
```python
APP_TITLE = "SOFT QUẢN LÝ XE V5.1.0"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800
DB_PATH = "vehicle_management.db"
```

---

#### **exceptions.py** - Định Nghĩa Lỗi
**Chức náng:**
- Định nghĩa các loại lỗi riêng của ứng dụng
- Giúp xử lý lỗi một cách có tổ chức

**Các loại lỗi chính:**
- `InvalidVINError` - VIN không hợp lệ
- `DuplicateVehicleError` - Xe đã tồn tại
- `InsufficientPermissionError` - Không có quyền
- `DatabaseError` - Lỗi cơ sở dữ liệu
- `BackupError` - Lỗi sao lưu

---

#### **utils.py** - Hàm Tiện Ích
**Chức năng:**
- Chứa các hàm dùng chung trong ứng dụng
- Xử lý ngày giờ, chuyển đổi dữ liệu, v.v.

**Ví dụ hàm tiện ích:**
```python
format_date(date) → "2026-01-14"
calculate_days_in_stock(date_in, date_out) → 45
is_valid_vin(vin) → True/False
```

---

### 📦 QUẢN LÝ XE (database/)

#### **vehicle_manager.py** - Quản Lý Thông Tin Xe ⭐ QUAN TRỌNG
**Chức năng:**
- Quản lý toàn bộ thông tin xe
- Thêm xe mới, cập nhật thông tin, xóa xe
- Theo dõi trạng thái xe (nhập kho, tuyệt chuyển, xuất kho, v.v.)

**Logic hoạt động chi tiết:**

**1. THÊM XE MỚI**
```
Người dùng nhập thông tin xe:
  - VIN (mã số xe)
  - Loại xe
  - Chủ sở hữu
  - Giá trị
  - Ngày nhập
    ↓
Ứng dụng kiểm tra:
  - VIN có hợp lệ không?
  - Xe đã tồn tại chưa?
  - Thông tin đầy đủ chưa?
    ↓
Nếu OK → Lưu vào CSDL + Ghi lại lịch sử
Nếu lỗi → Thông báo người dùng
```

**2. CẬP NHẬT TRẠNG THÁI XE**
```
Trạng thái xe thay đổi theo quy trình:

NHẬP KHO (date_in) 
   ↓
TRONG KHO (status = "in_stock")
   ↓
CHUYỂN GIAO (status = "transferred") ← Chuẩn bị vận chuyển
   ↓
XUẤT KHO (date_out) + Ghi lại địa điểm đến
   ↓
ĐÃ GIAO (status = "delivered")
```

**3. TÌMPM XE**
- Tìm theo VIN, chủ sở hữu, loại xe, địa điểm
- Hiển thị danh sách xe theo tiêu chí

**4. TÍNH TOÁN THÔNG TIN XE**
- Số ngày xe ở trong kho = ngày xuất - ngày nhập
- Tính mục tiêu tồn kho (stock level)
- Phân tích số lượng xe theo loại

---

#### **dispatch_manager.py** - Quản Lý Vận Chuyển
**Chức năng:**
- Tạo phiếu vận chuyển (gộp nhiều xe lại)
- Quản lý lô xe được vận chuyển
- Cập nhật trạng thái vận chuyển

**Logic hoạt động:**
```
QUYẾT TRÌNH VẬN CHUYỂN:

1. Tạo phiếu vận chuyển mới
   - Chọn địa điểm đích
   - Chọn loại vận chuyển
   - Ghi ghi chú
   
2. Thêm xe vào phiếu
   - Chọn xe từ kho
   - Xác nhận mỗi xe
   
3. Hoàn tất phiếu
   - Ký phiếu
   - Lưu thông tin người vận chuyển
   - Ghi lại ngày giờ
   
4. Theo dõi
   - Xem danh sách xe được vận chuyển
   - Cập nhật khi giao hàng thành công
```

---

#### **user_repository.py** - Quản Lý Tài Khoản Người Dùng
**Chức năng:**
- Quản lý tài khoản đăng nhập
- Kiểm tra mật khẩu
- Lưu trữ thông tin người dùng

**Logic hoạt động:**
```
QUYẾT TRÌNH ĐĂNG NHẬP:

1. Người dùng nhập username + password
   ↓
2. Ứng dụng kiểm tra:
   - Username có tồn tại?
   - Password có khớp?
   - Tài khoản có kích hoạt?
   ↓
3. Nếu OK → Đăng nhập thành công, ghi lại lịch sử
   Nếu lỗi → Thông báo lỗi, cấm đăng nhập sau 3 lần sai
```

---

#### **audit_repository.py** - Theo Dõi Lịch Sử Thay Đổi
**Chức năng:**
- Ghi lại MỌI thay đổi trong cơ sở dữ liệu
- Khi thêm xe → ghi lại ai, khi nào, thêm gì
- Khi cập nhật xe → ghi lại giá trị cũ + giá trị mới
- Khi xóa xe → ghi lại thông tin xe

**Ví dụ:**
```
Sự kiện 1: Người dùng "quanly01" thêm xe
  Thời gian: 2026-01-14 10:30
  Hành động: CREATE
  Dữ liệu: VIN=ABC123, Loại=SUV, Giá=500M

Sự kiện 2: Người dùng "quanly01" cập nhật giá
  Thời gian: 2026-01-14 11:00
  Hành động: UPDATE
  Thay đổi: Giá: 500M → 550M

Sự kiện 3: Người dùng "admin" xuất kho
  Thời gian: 2026-01-14 12:30
  Hành động: UPDATE
  Thay đổi: Trạng thái: in_stock → delivered
```

**Tại sao quan trọng?**
- Kiểm tra ai thay đổi dữ liệu
- Phát hiện các thay đổi trái phép
- Khôi phục dữ liệu nếu cần thiết

---

#### **location_manager.py** - Quản Lý Địa Điểm
**Chức năng:**
- Quản lý danh sách bãi xe, kho lưu trữ, điểm giao hàng
- Cập nhật số lượng xe ở từng địa điểm

**Logic hoạt động:**
```
Mỗi địa điểm (location) có:
- Tên địa điểm (Bãi Biên Hòa, Kho TP.HCM, v.v.)
- Địa chỉ chi tiết
- Người quản lý
- Công suất (tối đa bao nhiêu xe)
- Số lượng xe hiện tại
- Ngày cập nhật

Khi xe được vận chuyển:
  Bãi cũ: Giảm số lượng xe
  Bãi mới: Tăng số lượng xe
```

---

#### **entity_manager.py** - Quản Lý Thực Thể Chung
**Chức năng:**
- Quản lý các đối tượng khác không phải xe (nhà cung cấp, khách hàng, v.v.)
- Cung cấp hàm chung cho tất cả manager

---

#### **base_manager.py** - Kết Nối Cơ Sở Dữ Liệu
**Chức năng:**
- Quản lý kết nối đến cơ sở dữ liệu
- Đảm bảo chỉ có 1 kết nối (singleton pattern)
- Cung cấp phương thức thực thi truy vấn SQL

**Không cần chỉnh sửa:** Người dùng bỏ qua

---

### 🔐 XÁC THỰC & PHÂN QUYỀN (auth/)

#### **auth_manager.py** - Quản Lý Phiên Đăng Nhập
**Chức năng:**
- Theo dõi ai đã đăng nhập vào ứng dụng
- Lưu trữ thông tin người dùng hiện tại
- Kiểm tra quyền hạn của người dùng

**Logic hoạt động:**
```
Quy trình đăng nhập:

1. Người dùng nhập username + password vào LoginDialog
   ↓
2. AuthManager kiểm tra thông tin
   (Gọi UserRepository để xác minh)
   ↓
3. Nếu OK:
   - Lưu thông tin người dùng vào bộ nhớ
   - Ghi lại thời gian đăng nhập
   - Cho phép truy cập các tính năng
   
4. Khi người dùng đăng xuất:
   - Xóa thông tin người dùng khỏi bộ nhớ
   - Ghi lại thời gian đăng xuất

5. Kiểm tra quyền:
   - Người dùng muốn thêm xe → Kiểm tra có quyền không?
   - Nếu không → Hiển thị "Không có quyền"
```

**3 loại người dùng:**
1. **Admin** - Toàn quyền, quản lý tất cả
2. **Operator** - Quản lý xe, vận chuyển, không được quản lý người dùng
3. **Viewer** - Chỉ xem, không được sửa đổi

---

#### **permissions.py** - Định Nghĩa Quyền Hạn
**Chức năng:**
- Liệt kê tất cả quyền hạn trong ứng dụng (30+ quyền)
- Gán quyền hạn cho từng loại người dùng

**Ví dụ quyền hạn:**
- `ADD_VEHICLE` - Thêm xe mới
- `EDIT_VEHICLE` - Sửa thông tin xe
- `DELETE_VEHICLE` - Xóa xe
- `CREATE_DISPATCH` - Tạo phiếu vận chuyển
- `MANAGE_USERS` - Quản lý tài khoản
- `VIEW_AUDIT_LOG` - Xem lịch sử thay đổi
- `BACKUP_DATABASE` - Sao lưu dữ liệu

**Bảng quyền hạn:**
```
┌─────────────────────┬───────┬──────────┬────────┐
│ Quyền hạn           │ Admin │ Operator │ Viewer │
├─────────────────────┼───────┼──────────┼────────┤
│ ADD_VEHICLE         │  ✓    │    ✓     │   ✗    │
│ EDIT_VEHICLE        │  ✓    │    ✓     │   ✗    │
│ DELETE_VEHICLE      │  ✓    │    ✓     │   ✗    │
│ CREATE_DISPATCH     │  ✓    │    ✓     │   ✗    │
│ MANAGE_USERS        │  ✓    │    ✗     │   ✗    │
│ VIEW_AUDIT_LOG      │  ✓    │    ✓     │   ✓    │
│ BACKUP_DATABASE     │  ✓    │    ✗     │   ✗    │
└─────────────────────┴───────┴──────────┴────────┘
```

---

### ⚙️ CÁC DỊCH VỤ BACKEND (core/)

#### **backup_service.py** - Sao Lưu & Khôi Phục Dữ Liệu
**Chức năng:**
- Tạo bản sao lưu (backup) của cơ sở dữ liệu
- Khôi phục (restore) từ bản sao lưu cũ
- Xác minh độ toàn vẹn của bản sao lưu

**Logic hoạt động:**

**1. Tạo bản sao lưu:**
```
Người dùng nhấn "Sao lưu"
   ↓
Hệ thống:
  - Tạo sao chép toàn bộ cơ sở dữ liệu
  - Nén file (gzip)
  - Lưu vào thư mục backups/
  - Ghi metadata (ngày tạo, kích thước, checksum)
  - Thông báo "Sao lưu thành công"
```

**2. Tự động sao lưu trước khi:**
- Xuất kho (trước khi cập nhật trạng thái)
- Xóa dữ liệu
- Tạo báo cáo lớn

**3. Khôi phục dữ liệu:**
```
Người dùng chọn "Khôi phục từ bản sao"
   ↓
Hệ thống:
  - Hiển thị danh sách bản sao cũ
  - Người dùng chọn bản sao muốn khôi phục
  - Tạo backup của CSDL hiện tại (an toàn)
  - Khôi phục từ bản sao cũ
  - Xác minh dữ liệu
  - Thông báo "Khôi phục thành công"
```

**Tại sao quan trọng?**
- Nếu xóa sai dữ liệu → Có thể khôi phục
- Nếu hệ thống sập → Không mất dữ liệu
- Bản sao lưu theo định kỳ (hàng ngày, hàng tuần)

---

#### **notification_service.py** - Gửi Thông Báo
**Chức năng:**
- Gửi thông báo cho người dùng
- Ghi lại thông báo

**Ví dụ thông báo:**
- "Xe ABC123 đã được thêm thành công"
- "Phiếu vận chuyển DIS001 đã hoàn tất"
- "Cảnh báo: Kho sắp đầy (95% công suất)"
- "Lỗi: Không thể xuất kho xe XYZ789"

---

### 🎨 GIAO DIỆN NGƯỜI DÙNG (ui/)

#### **login_dialog.py** - Cửa Sổ Đăng Nhập
**Chức năng:**
- Hiển thị cửa sổ đăng nhập khi khởi động
- Lấy username + password từ người dùng
- Gửi thông tin đến AuthManager để kiểm tra

**Logic hoạt động:**
```
Người dùng chạy ứng dụng
   ↓
Hiển thị cửa sổ đăng nhập
   ↓
Người dùng nhập username + password
   ↓
Người dùng nhấn "Đăng nhập"
   ↓
Ứng dụng kiểm tra:
  - Username có tồn tại?
  - Password có đúng?
   ↓
Nếu đúng → Đóng cửa sổ, mở giao diện chính
Nếu sai → Hiển thị lỗi, cho nhập lại
```

---

#### **dashboard_tab.py** - Trang Chủ
**Chức năng:**
- Hiển thị thông tin tóm tắt của ứng dụng
- Số lượng xe tổng cộng
- Xe trong kho
- Phiếu vận chuyển chưa hoàn tất
- Biểu đồ thống kê

**Thông tin hiển thị:**
```
TRANG CHỦ
═══════════════════════════════════════

📊 Thống Kê Tổng Quát
  • Tổng số xe:           1,245 xe
  • Xe trong kho:         856 xe
  • Xe đã xuất:           389 xe
  • Tỷ lệ kho:            68.7%

📈 Biểu Đồ
  - Số lượng xe theo loại (pie chart)
  - Xu hướng nhập/xuất (line chart)
  - Top 5 bãi có xe nhiều nhất

⚠️ Cảnh Báo
  - Kho Biên Hòa: 95% công suất
  - 5 phiếu vận chuyển chưa hoàn tất
```

---

#### **stock_tab.py** - Quản Lý Kho
**Chức năng:**
- Xem danh sách tất cả xe trong kho
- Sắp xếp, lọc xe theo tiêu chí
- Xem chi tiết thông tin xe từng cái

**Thông tin hiển thị:**
```
DANH SÁCH XE TRONG KHO
═══════════════════════════════════════

VIN         │ Loại   │ Chủ SH  │ Ngày Nhập  │ Giá
────────────┼────────┼─────────┼────────────┼──────
ABC123      │ SUV    │ Công ty A│ 2025-12-01│ 500M
XYZ789      │ Sedan  │ Công ty B│ 2025-12-15│ 350M
DEF456      │ SUV    │ Công ty A│ 2026-01-05│ 550M
...
```

---

#### **inbound_tab.py** - Nhập Xe
**Chức năng:**
- Thêm xe mới vào kho
- Nhập thông tin chi tiết xe
- Lưu thông tin chủ sở hữu

**Quy trình nhập xe:**
```
1. Nhấn nút "Thêm Xe"
2. Nhập thông tin:
   - VIN (mã số xe)
   - Loại xe (SUV, Sedan, v.v.)
   - Chủ sở hữu
   - Giá tiền
   - Ngày nhập
   - Ghi chú
3. Kiểm tra thông tin
4. Lưu vào kho
```

---

#### **outbound_tab.py** - Xuất Xe
**Chức năng:**
- Xuất xe khỏi kho
- Cập nhật trạng thái xe
- Ghi lại nơi giao hàng

**Quy trình xuất xe:**
```
1. Chọn xe cần xuất từ danh sách
2. Nhập thông tin xuất:
   - Nơi giao hàng
   - Người nhận
   - Ngày xuất
   - Loại vận chuyển
3. Kiểm tra thông tin
4. Hoàn tất xuất kho
```

---

#### **dispatch_tab.py** - Quản Lý Vận Chuyển
**Chức năng:**
- Tạo phiếu vận chuyển
- Thêm xe vào phiếu
- Theo dõi trạng thái vận chuyển

**Quy trình tạo phiếu vận chuyển:**
```
1. Nhấn nút "Tạo Phiếu Mới"
2. Chọn thông tin:
   - Nơi đích vận chuyển
   - Loại vận chuyển
   - Ngày dự kiến
3. Chọn xe từ kho để thêm vào phiếu
4. Xác nhận danh sách xe
5. Hoàn tất phiếu
6. In phiếu vận chuyển
```

---

#### **yard_map_tab.py** - Bản Đồ Bãi
**Chức năng:**
- Hiển thị bản đồ các bãi xe
- Xem số lượng xe ở từng bãi
- Theo dõi không gian còn trống

**Thông tin hiển thị:**
```
BẢN ĐỒ BÃI XE
═══════════════════════════════════════

🏢 Bãi Biên Hòa: 450/500 xe (90%)
🏢 Kho TP.HCM: 250/300 xe (83%)
🏢 Bãi Đà Nẵng: 156/200 xe (78%)
```

---

#### **search_tab.py** - Tìm Kiếm Nâng Cao
**Chức năng:**
- Tìm kiếm xe theo nhiều tiêu chí
- Lọc xe theo loại, giá, ngày, v.v.

**Ví dụ tìm kiếm:**
- Tìm xe SUV nhập từ 2025-12-01 đến 2026-01-14
- Tìm xe của Công ty A có giá > 500M
- Tìm xe trong kho Biên Hòa

---

#### **log_tab.py** - Xem Lịch Sử
**Chức năng:**
- Xem lịch sử tất cả thay đổi trong ứng dụng
- Lọc theo người dùng, hành động, ngày

**Thông tin hiển thị:**
```
LỊCH SỬ THAY ĐỔI
═══════════════════════════════════════

Thời gian        │ Người dùng  │ Hành động │ Chi tiết
────────────────┼────────────┼──────────┼──────────────
2026-01-14 10:30│ quanly01   │ ADD      │ Xe ABC123
2026-01-14 11:00│ quanly01   │ EDIT     │ Cập nhật giá
2026-01-14 12:30│ quanly02   │ DELETE   │ Xóa xe XYZ
```

---

#### **archive_explorer_dialog.py** - Duyệt Kho Lưu Trữ
**Chức năng:**
- Xem các bản sao lưu cũ
- Khôi phục từ bản sao lưu

---

#### **user_management_dialog.py** - Quản Lý Người Dùng
**Chức năng:**
- Thêm/xóa người dùng (chỉ Admin)
- Cập nhật quyền hạn
- Đặt lại mật khẩu

**Quy trình thêm người dùng:**
```
1. Nhấn nút "Thêm Người Dùng"
2. Nhập thông tin:
   - Tên đăng nhập
   - Tên đầy đủ
   - Mật khẩu
   - Loại (Admin/Operator/Viewer)
3. Lưu người dùng mới
```

---

#### **voucher_creation_dialog.py** - Tạo Phiếu
**Chức năng:**
- Tạo phiếu vận chuyển
- In phiếu (PDF, Excel)
- Quản lý thông tin phiếu

---

#### **components.py** - Các Thành Phần UI
**Chức năng:**
- Định nghĩa các thành phần giao diện (nút, bảng, v.v.)
- Không cần chỉnh sửa

---

#### **layout_manager.py** - Quản Lý Bố Cục
**Chức năng:**
- Quản lý cách sắp xếp các thành phần trên màn hình
- Không cần chỉnh sửa

---

### 📊 CÔNG CỤ BÁO CÁO (report_generators/)

#### **excel_generator.py** - Tạo Báo Cáo Excel
**Chức năng:**
- Xuất dữ liệu ra file Excel (.xlsx)
- Tạo biểu đồ trong Excel
- Định dạng màu sắc, font

**Ví dụ báo cáo Excel:**
```
Báo Cáo Quản Lý Kho - Tháng 1/2026
════════════════════════════════════

Tổng số xe:           1,245 xe
Xe trong kho:         856 xe
Xe đã giao:           389 xe

Chi tiết theo loại:
  Loại    │ Số lượng │ Giá trị
  ────────┼──────────┼───────────
  SUV     │   520    │ 260 tỷ
  Sedan   │   450    │ 157 tỷ
  ...
```

---

#### **pdf_generator.py** - Tạo Báo Cáo PDF
**Chức năng:**
- Xuất dữ liệu ra file PDF
- Tạo báo cáo đẹp, sẵn sàng in

---

#### **word_generator.py** - Tạo Báo Cáo Word
**Chức năng:**
- Xuất dữ liệu ra file Word (.docx)
- Tạo báo cáo chi tiết

---

### 📈 QUẢN LÝ BÁO CÁO (reporting/)

#### **central_report.py** - Tạo Báo Cáo Toàn Hệ Thống
**Chức năng:**
- Tạo báo cáo tổng hợp từ tất cả dữ liệu
- Báo cáo hiệu suất kho

---

#### **central_event_store.py** - Lưu Trữ Sự Kiện
**Chức năng:**
- Lưu lịch sử tất cả sự kiện quan trọng
- Để phục vụ báo cáo

---

#### **central_transfer_report.py** - Báo Cáo Vận Chuyển
**Chức năng:**
- Tạo báo cáo vận chuyển
- Thống kê xe đã giao

---

### 🛠️ CÔNG CỤ TIỆN ÍCH (tools/)

Các công cụ dòng lệnh để:
- Tạo báo cáo từ terminal
- Nhập/xuất dữ liệu

---

## ⚙️ Các Tệp Cấu Hình

### **config.ini** - Cấu Hình Chung
```ini
[Database]
path = vehicle_management.db
auto_backup = true

[UI]
theme = light
language = vi

[Backup]
frequency = daily
retention_days = 30
```

### **owner_map.json** - Ánh Xạ Chủ Xe
```json
{
  "Công ty A": "company_a",
  "Công ty B": "company_b",
  "...": "..."
}
```

---

## 🔄 Cách Thức Hoạt Động - Toàn Cảnh

### **Quy Trình Nhập Xe Chi Tiết**

```
         ┌─────────────────────────────────┐
         │  Người dùng chạy main.py        │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Hiển thị cửa sổ đăng nhập      │
         │  (login_dialog.py)              │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Kiểm tra username + password   │
         │  (auth_manager.py)              │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Hiển thị giao diện chính       │
         │  (dashboard_tab.py)             │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Người dùng chọn "Nhập Xe"      │
         │  (inbound_tab.py)               │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Nhập thông tin xe:             │
         │  - VIN, loại, chủ sở hữu, v.v. │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Kiểm tra dữ liệu               │
         │  (data_normalizer.py)           │
         │  - VIN hợp lệ?                  │
         │  - Xe trùng lặp?                │
         │  - Thông tin đầy đủ?            │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Lưu vào cơ sở dữ liệu          │
         │  (vehicle_manager.py)           │
         │  + Tạo backup tự động           │
         │  (backup_service.py)            │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Ghi lại lịch sử                │
         │  (audit_repository.py)          │
         │  "Xe ABC123 đã được thêm"       │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Hiển thị thông báo             │
         │  (notification_service.py)      │
         │  "Thêm xe thành công!"          │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Cập nhật danh sách kho         │
         │  (stock_tab.py)                 │
         └─────────────────────────────────┘
```

### **Quy Trình Xuất Xe Chi Tiết**

```
         ┌─────────────────────────────────┐
         │  Người dùng chọn "Xuất Xe"      │
         │  (outbound_tab.py)              │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Chọn xe từ danh sách kho       │
         │  (vehicle_manager.py)           │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Nhập nơi giao hàng             │
         │  (location_manager.py)          │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Tạo phiếu vận chuyển           │
         │  (dispatch_manager.py)          │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Tạo backup trước cập nhật      │
         │  (backup_service.py)            │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Cập nhật trạng thái xe         │
         │  status = "delivered"           │
         │  (vehicle_manager.py)           │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Cập nhật số lượng bãi          │
         │  (location_manager.py)          │
         │  Bãi cũ: -1 xe                  │
         │  Bãi mới: +1 xe                 │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Ghi lại lịch sử                │
         │  (audit_repository.py)          │
         │  "Xe ABC123 đã xuất"            │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  Gửi thông báo                  │
         │  (notification_service.py)      │
         │  "Xuất xe thành công!"          │
         └────────────┬────────────────────┘
                      │
         ┌────────────▼────────────────────┐
         │  In phiếu vận chuyển (PDF)      │
         │  (pdf_generator.py)             │
         └─────────────────────────────────┘
```

---

## 🎓 Tóm Tắt Cho Người Dùng Cuối

**Để hiểu cách ứng dụng hoạt động:**

1. **Bắt đầu:** Đọc phần "Tổng Quan Ứng Dụng"
2. **Hiểu cấu trúc:** Xem sơ đồ "Cấu Trúc Thư Mục"
3. **Tìm file cần thiết:** Sử dụng "Giải Thích Chi Tiết Từng File"
4. **Tìm hiểu quy trình:** Xem phần "Cách Thức Hoạt Động"

**Các file QUAN TRỌNG nhất:**
- `main.py` - Khởi động ứng dụng
- `database/vehicle_manager.py` - Quản lý xe
- `database/dispatch_manager.py` - Quản lý vận chuyển
- `auth/auth_manager.py` - Kiểm tra quyền
- `core/backup_service.py` - Sao lưu dữ liệu

**Nếu gặp lỗi:**
- Kiểm tra file `app_log.txt` để xem nhật ký lỗi
- Xem `database/audit_repository.py` để kiểm tra lịch sử thay đổi
- Khôi phục từ bản sao lưu nếu cần (dùng `backup_service.py`)

---

## 📞 Liên Hệ Hỗ Trợ

Nếu có câu hỏi về:
- **Cách sử dụng ứng dụng** → Xem file `User_Guide.md`
- **Cách hoạt động chi tiết** → Xem file này (`APPLICATION_STRUCTURE_USER_GUIDE.md`)
- **Kế hoạch phát triển** → Xem file `ROADMAP.md`
- **Lỗi hoặc sự cố** → Kiểm tra `app_log.txt` hoặc liên hệ đội phát triển

---

**Cập nhật: 2026-01-14**
**Phiên bản: V5.1.0**
