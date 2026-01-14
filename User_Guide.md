
# HƯỚNG DẪN SỬ DỤNG CHO NGƯỜI DÙNG CUỐI (BẢN .EXE)

> **Phiên bản:** V5.2.0 | **Cập nhật:** 15/01/2026 | **Trạng thái:** ✅ Production

Tài liệu này hướng dẫn sử dụng phần mềm Quản lý Xe dành cho nhân viên, người dùng cuối (không cần thao tác kỹ thuật, chỉ cần chạy file .exe).

---

## BẮT ĐẦU NHANH VỚI PHẦN MỀM (.EXE)

1. Tải file **SOFT_QUAN_LY_XE_V5.1.0.exe** từ bộ phận IT hoặc link được cung cấp
2. Giải nén (nếu là file .zip) vào một thư mục trên máy tính
3. Nhấp đúp vào file **SOFT_QUAN_LY_XE_V5.1.0.exe** để chạy phần mềm
4. Lần đầu chạy, phần mềm sẽ tự tạo các file dữ liệu cần thiết

> **Lưu ý:**
>
> - Không xóa các file .db, .ini, logs... trong thư mục phần mềm
> - Nếu phần mềm bị chặn bởi Windows Defender, chọn "More info" → "Run anyway"
> - Nếu gặp lỗi, liên hệ bộ phận hỗ trợ (xem cuối tài liệu)

### Đăng nhập lần đầu

- Tài khoản mặc định:
   -Username: `admin`
   -Password: `admin123`
  
- Đổi mật khẩu admin ngay sau lần đăng nhập đầu tiên

---

## CÁC CHỨC NĂNG ĐÃ HOÀN THIỆN (V5.2.0)

### Nghiệp vụ cốt lõi
- Nhập bãi: Thủ công hoặc import Excel
- Xuất bãi: Theo phiếu (nhiều xe) hoặc xuất lẻ
- Tồn bãi: Quản lý, tìm kiếm, chỉnh sửa, đổi vị trí, xóa mềm
- Bản đồ bãi: Xem slot trống/có xe, zoom, filter, click-to-view
- Tra cứu nâng cao: Lọc theo ngày, trạng thái, block, chủ hàng

### Quản trị & Bảo mật
- Đăng nhập 3 vai trò (Admin/Supervisor/Operator)
- Audit Log: Ghi lại mọi thao tác
- Backup/Restore: Sao lưu thủ công & tự động, khôi phục an toàn

### Tiện ích
- Phím tắt phổ biến: F5, Ctrl+N/F/E/D/M/B/Q
- Auto-complete VIN, Chủ hàng
- Thông báo: Xe tồn lâu, bãi sắp đầy, hệ thống
- Đa ngôn ngữ: Tiếng Việt / English
- Báo cáo: Excel, PDF, Word với biểu đồ

### 🆕 Tính năng HQ - Tổng hợp nhiều bãi (Phase 3)
- **Gửi dữ liệu về HQ**: Các bãi xuất dữ liệu gửi về Tổng công ty
- **Nhận dữ liệu từ bãi**: HQ nhận và tổng hợp dữ liệu từ nhiều bãi
- **Tạo báo cáo tổng hợp**: Báo cáo hoạt động xe, tổng hợp theo bãi, đối soát chuyển bãi
- **Khử trùng tự động**: Tự động loại bỏ trùng lặp khi xe chuyển giữa các bãi

<!-- HƯỚNG DẪN CHI TIẾT (THAO TÁC CƠ BẢN) -->

## Mục lục

1. [Tổng quan giao diện](#1-tổng-quan-giao-diện)
2. [Đăng nhập & Phân quyền](#2-đăng-nhập--phân-quyền)
3. [Quy trình làm việc](#3-quy-trình-làm-việc)
4. [Bản đồ bãi xe](#4-bản-đồ-bãi-xe)
5. [Thông báo & Cảnh báo](#5-thông-báo--cảnh-báo)
6. [Phím tắt](#6-phím-tắt)
7. [Backup & Restore](#7-backup--restore)
8. [Báo cáo](#8-báo-cáo)
9. [Cài đặt & Công cụ](#9-cài-đặt--công-cụ)
10. [Xử lý lỗi](#10-xử-lý-lỗi)

---

## 1) Tổng quan giao diện

Ứng dụng được chia thành các tab chức năng:

- **Nhập bãi**: Thêm xe vào bãi (nhập thủ công hoặc import Excel). Hệ thống tự gán vị trí trống nếu chọn tự động.
- **🚚 Xuất bãi (nhiều)**: Tạo và xử lý một phiếu xuất (Dispatch) cho nhiều xe; thêm xe bằng cách quét/nhập VIN.
- **Xuất bãi (lẻ)**: Xuất nhanh một xe riêng lẻ (trường hợp không theo phiếu).
- **Tồn bãi**: Danh sách xe đang trong bãi; lọc theo chủ hàng, tìm kiếm, thao tác chuột phải để chỉnh sửa/đảo vị trí/xóa (ẩn).
- **🔍 Tra cứu**: Tìm kiếm nhanh theo VIN/chủ hàng/thuộc tính; dùng để tra lại dữ liệu đã nhập/xuất.
- **📊 Báo cáo**: Xem biểu đồ và xuất báo cáo (PNG/PDF) theo khoảng thời gian.
- **Nhật ký hoạt động**: Theo dõi các thao tác và thông báo hệ thống.

## 2) Đăng nhập & Phân quyền

### 2.1 Đăng nhập

Khi khởi động ứng dụng, màn hình đăng nhập sẽ hiển thị:

1. Nhập **Tên đăng nhập** và **Mật khẩu**
2. Nhấn **Đăng nhập** hoặc Enter

> ⚠️ **Lưu ý:** Đổi mật khẩu admin ngay sau lần đăng nhập đầu tiên!

### 2.2 Vai trò & Quyền hạn

| Vai trò | Mô tả | Quyền chính |
| --- | --- | --- |
| **Admin** | Quản trị viên | Toàn quyền: quản lý user, backup, cấu hình |
| **Supervisor** | Giám sát viên | Xem tất cả, xuất báo cáo, không quản lý user |
| **Operator** | Nhân viên vận hành | Nhập/xuất xe, xem tồn, không xóa |

### 2.3 Quản lý người dùng (Admin)

1. Menu **Cài đặt** → **Quản lý người dùng**
2. Thêm/Sửa/Xóa/Khóa tài khoản
3. Đổi mật khẩu, phân vai trò

---

## 3) Quy trình làm việc

### 3.1 Nhập xe vào bãi

#### Cách A — Nhập thủ công

1. Vào tab **Nhập bãi**
2. Nhập **Số khung (VIN)**, **Chủ hàng**, **Loại xe**
3. Chọn vị trí hoặc nhấn **Tự động tìm** để lấy vị trí trống
4. Nhấn **Lưu** để hoàn tất

> 💡 **Tip:** Trường Chủ hàng có **Auto-complete** - gõ vài ký tự để xem gợi ý

#### Cách B — Import Excel (hàng loạt)

1. Vào tab **Nhập bãi** → khung **Nhập hàng loạt (Excel)**
2. Nhấn **Import Excel** và chọn file
3. Hệ thống sẽ tự dò tên cột và import; nếu có lỗi/thiếu cột, phần mềm sẽ báo chi tiết

### 3.2 Xuất bãi theo phiếu (nhiều xe)

1. Vào tab **🚚 Xuất bãi (nhiều)**
2. Chọn **Tài xế** và **Xe vận chuyển**
3. Nhấn **Tạo phiếu**
4. Quét/nhập VIN để thêm xe vào phiếu
5. Nhấn **Hoàn tất** để xuất bãi

### 3.3 Xuất bãi lẻ (một xe)

1. Vào tab **Xuất bãi (lẻ)**
2. Quét/nhập VIN
3. Nhấn **Xuất**

### 3.4 Tra cứu nâng cao

1. Vào tab **🔍 Tra cứu**
2. Sử dụng các filter:
   - **Từ ngày / Đến ngày**
   - **Trạng thái**: Tất cả / Tồn bãi / Đã xuất
   - **Block**: Lọc theo khu vực
   - **VIN / Chủ hàng**: Tìm kiếm text

> 💡 **Tip:** Các trường VIN, Chủ hàng có **Auto-complete**

---

## 4) Bản đồ bãi xe

Tab **🗺️ Bản đồ bãi** hiển thị visualization 2D của bãi:

### Màu sắc slot

- 🟢 **Xanh lá**: Slot trống
- 🔴 **Đỏ**: Có xe
- 🟡 **Vàng**: Đang chọn
- 🔵 **Xanh dương**: Di chuột hover

### Thao tác

- **Click** vào slot để xem chi tiết xe
- **Zoom In/Out** với các nút hoặc scroll
- **Filter** theo Block, Trạng thái

---

## 5) Thông báo & Cảnh báo

### 5.1 Biểu tượng chuông 🔔

- Góc trên bên phải màn hình
- Badge số đỏ = số thông báo chưa đọc
- Click để mở panel thông báo

### 5.2 Loại thông báo

| Loại | Mô tả |
| --- | --- |
| ⚠️ **Xe tồn lâu** | Xe ở bãi quá số ngày quy định |
| 🚨 **Bãi sắp đầy** | Sức chứa đạt ngưỡng cảnh báo |
| ℹ️ **Hệ thống** | Backup thành công, cập nhật... |

### 5.3 Cài đặt thông báo

Menu **Cài đặt** → **Cài đặt thông báo**:

- Bật/tắt Toast popup
- Bật/tắt âm thanh
- Điều chỉnh ngưỡng ngày tồn

---

## 6) Phím tắt

| Phím | Chức năng |
| --- | --- |
| **F5** | Làm mới tab hiện tại |
| **Ctrl+N** | Đến tab Nhập bãi |
| **Ctrl+F** | Đến tab Tra cứu |
| **Ctrl+E** | Xuất dữ liệu |
| **Ctrl+D** | Đến tab Dispatch |
| **Ctrl+M** | Đến tab Bản đồ bãi |
| **Ctrl+B** | Đến tab Dashboard |
| **Ctrl+Q** | Đăng xuất |
| **Escape** | Xóa selection/filter |

---

## 7) Backup & Restore

### 7.1 Tạo backup thủ công

1. Menu **Công cụ** → **Backup & Restore**
2. Nhấn **Tạo backup**
3. Backup được lưu vào `backups/manual/`

### 7.2 Khôi phục từ backup

1. Mở dialog **Backup & Restore**
2. Chọn backup từ danh sách
3. Nhấn **Khôi phục**
4. Xác nhận để tiếp tục

> ⚠️ Hệ thống sẽ tự động backup trước khi restore để an toàn

### 7.3 Xác minh backup

- Nhấn **Verify** để kiểm tra tính toàn vẹn của backup
- Hệ thống kiểm tra checksum SHA-256

---

## 8) Báo cáo

Tab **📊 Báo cáo** cho phép:

1. Chọn khoảng thời gian
2. Nhấn **Cập nhật** để xem biểu đồ
3. Xuất:

   - **PNG**: Ảnh biểu đồ
   - **PDF**: Báo cáo đầy đủ
   - **Excel**: Dữ liệu chi tiết

---

## 9) Cài đặt & Công cụ

### 9.1 Tính năng HQ - Tổng hợp nhiều bãi (Phase 3)

Các tính năng dành cho **Tổng công ty (HQ)** để tổng hợp dữ liệu từ nhiều bãi xe.

#### A. Dành cho người dùng (Giao diện)

Trên tab **📊 Báo cáo**, có 3 nút công cụ:

| Nút | Chức năng | Mô tả |
| --- | --- | --- |
| **Gửi dữ liệu về HQ** | Xuất dữ liệu | Bãi xe xuất file .zip gửi về Tổng công ty |
| **Nhận dữ liệu từ bãi** | Nhận dữ liệu | HQ import file .zip từ các bãi |
| **Tạo báo cáo** | Tạo báo cáo tổng hợp | Sinh báo cáo từ dữ liệu đã nhận |

**Quy trình sử dụng:**

1. **Tại các bãi xe:**
   - Click **"Gửi dữ liệu về HQ"**
   - Chọn khoảng thời gian cần xuất
   - Chọn thư mục lưu file
   - Gửi file .zip cho Tổng công ty (email, USB, mạng nội bộ...)

2. **Tại Tổng công ty (HQ):**
   - Click **"Nhận dữ liệu từ bãi"**
   - Chọn các file .zip nhận được từ các bãi
   - Hệ thống tự động import và tổng hợp

3. **Tạo báo cáo:**
   - Click **"Tạo báo cáo"**
   - Chọn loại báo cáo:
     - *Hoạt động xe*: Chi tiết từng xe vào/ra
     - *Tổng hợp theo bãi*: Thống kê theo từng bãi
     - *Đối soát chuyển bãi*: Kiểm tra xe chuyển giữa các bãi
     - *Tổng hợp (Tất cả)*: Báo cáo đầy đủ
   - Bật **"Khử trùng"** để tự động loại bỏ trùng lặp

#### B. Dành cho IT (Command Line)

```bash
# Theo dõi thư mục và tự động import
python -m tools.hq_automation --monitor

# Import một lần tất cả file mới
python -m tools.hq_automation --batch

# Tạo Task Scheduler chạy tự động hàng ngày (02:00)
python -m tools.hq_automation --setup-task
```

**Thư mục mặc định:**
- Monitor: `data/monitor`
- Imports: `data/imports`
- Logs: `logs/automation`

> **Lưu ý:** File đang ghi dở (.tmp) sẽ được bỏ qua; file lỗi sẽ chuyển sang `_errors`.

### Menu Cài đặt

| Mục | Mô tả |
| --- | --- |
| Quản lý tài xế | Thêm/Sửa/Xóa tài xế |
| Quản lý xe vận chuyển | Thêm/Sửa/Xóa xe VC |
| Quản lý Layout bãi | Định nghĩa cấu trúc bãi |
| Quản lý người dùng | Thêm/Sửa user (Admin) |
| Cài đặt thông báo | Tùy chỉnh notification |
| Chọn mẫu phiếu | Chọn template .docx |
| Lưu trữ dữ liệu | Archive dữ liệu cũ |

### Menu Công cụ

| Mục | Mô tả |
| --- | --- |
| Tạo phiếu vận chuyển | Tạo file phiếu in |
| Tra cứu lưu trữ | Xem dữ liệu archive |
| Backup & Restore | Sao lưu/Khôi phục |
| Xe đã xóa | Xem/Khôi phục xe soft-delete |

---

## 10) Xử lý lỗi

| Lỗi | Nguyên nhân | Giải pháp |
| --- | --- | --- |
| Không import được Excel | Thiếu cột bắt buộc | Kiểm tra cột VIN/Chủ hàng/Loại xe |
| Không thêm được VIN | VIN đã tồn tại | Tra cứu trong tab **🔍 Tra cứu** |
| Không tạo được phiếu | Thiếu thông tin | Chọn đủ Tài xế và Xe VC |
| Báo cáo trống | Không có dữ liệu | Mở rộng khoảng thời gian |
| Đăng nhập thất bại | Sai thông tin | Kiểm tra username/password |
| Tài khoản bị khóa | Nhập sai >5 lần | Liên hệ Admin để mở khóa |

---

## Liên hệ hỗ trợ

- **Email:** [support@example.com](mailto:support@example.com)
- **Hotline:** 1900-xxxx
- **Tài liệu:** Xem thêm [README.md](README.md), [CHANGELOG.md](CHANGELOG.md)
