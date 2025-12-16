# Hướng dẫn Sử dụng Phần mềm Quản lý Xe - V5.0

Tài liệu này hướng dẫn cách sử dụng các chức năng chính của ứng dụng Quản lý Xe (V5.0).

## 1) Tổng quan giao diện

Ứng dụng được chia thành các tab chức năng:

- **Nhập bãi**: Thêm xe vào bãi (nhập thủ công hoặc import Excel). Hệ thống tự gán vị trí trống nếu chọn tự động.
- **🚚 Xuất bãi (nhiều)**: Tạo và xử lý một phiếu xuất (Dispatch) cho nhiều xe; thêm xe bằng cách quét/nhập VIN.
- **Xuất bãi (lẻ)**: Xuất nhanh một xe riêng lẻ (trường hợp không theo phiếu).
- **Tồn bãi**: Danh sách xe đang trong bãi; lọc theo chủ hàng, tìm kiếm, thao tác chuột phải để chỉnh sửa/đảo vị trí/xóa (ẩn).
- **🔍 Tra cứu**: Tìm kiếm nhanh theo VIN/chủ hàng/thuộc tính; dùng để tra lại dữ liệu đã nhập/xuất.
- **📊 Báo cáo**: Xem biểu đồ và xuất báo cáo (PNG/PDF) theo khoảng thời gian.
- **Nhật ký hoạt động**: Theo dõi các thao tác và thông báo hệ thống.

## 2) Quy trình làm việc khuyến nghị

### 2.1 Nhập xe vào bãi

#### Cách A — Nhập thủ công

1. Vào tab **Nhập bãi**.
2. Nhập **Số khung (VIN)**, **Chủ hàng**, **Loại xe**.
3. Chọn vị trí hoặc nhấn **Tự động tìm** để lấy vị trí trống.
4. Nhấn **Lưu** để hoàn tất.

#### Cách B — Import Excel (hàng loạt)

1. Vào tab **Nhập bãi** → khung **Nhập hàng loạt (Excel)**.
2. Nhấn **Import Excel** và chọn file.
3. Hệ thống sẽ tự dò tên cột và import; nếu có lỗi/thiếu cột, phần mềm sẽ báo chi tiết.

Lưu ý:

- Import sẽ báo các VIN trùng trong chính file Excel (để bạn sửa trước khi import lại).

### 2.2 Xuất bãi theo phiếu (nhiều xe)

1. Vào tab **🚚 Xuất bãi (nhiều)**.
2. Chọn **Tài xế** và **Xe vận chuyển**.
3. Nhấn **Tạo phiếu**.
4. Ở ô quét/nhập VIN, lần lượt **quét hoặc nhập VIN** để thêm xe vào phiếu.
5. Nhấn **Hoàn tất** để xuất bãi toàn bộ xe trong phiếu.

Ghi chú:

- Nếu VIN không ở trạng thái tồn bãi hoặc đã được thêm vào phiếu, hệ thống sẽ cảnh báo.
- Có thể **Hủy phiếu** để trả xe về trạng thái tồn bãi.

### 2.3 Xuất bãi lẻ (một xe)

1. Vào tab **Xuất bãi (lẻ)**.
2. Quét/nhập VIN.
3. Nhấn **Xuất** để hoàn tất.

### 2.4 Quản lý tồn bãi

1. Vào tab **Tồn bãi**.
2. Dùng lọc theo **Chủ hàng**, hoặc tìm theo VIN/Chủ hàng.
3. Chuột phải lên một dòng để:
   - **Chỉnh sửa thông tin**
   - **Đảo vị trí**
   - **Xóa xe (ẩn)**

## 3) Báo cáo

- Tab **📊 Báo cáo** cho phép chọn khoảng thời gian, nhấn **Cập nhật**.
- Có thể xuất:
  - **Xuất ảnh PNG**
  - **Xuất báo cáo PDF**
- Có thể bật **Tự động làm mới** theo phút.

## 4) Menu Cài đặt & Công cụ

Trên thanh menu:

### Cài đặt

- **Quản lý tài xế**: thêm/sửa/xóa tài xế.
- **Quản lý xe vận chuyển**: thêm/sửa/xóa xe vận chuyển.
- **Quản lý Layout bãi xe**: định nghĩa/cập nhật cấu trúc vị trí bãi.
- **Chọn mẫu phiếu vận chuyển**: chọn file `.docx` template dùng khi tạo phiếu.
- **Lưu trữ dữ liệu**: lưu trữ & xóa dữ liệu xe đã xuất trong khoảng thời gian (tạo file archive).

### Công cụ

- **Tạo phiếu vận chuyển**: tạo file phiếu theo mẫu cho nhu cầu in ấn.
- **Tra cứu lưu trữ**: chọn file archive và xuất dữ liệu lưu trữ ra Excel theo khoảng thời gian.

## 5) Lưu trữ dữ liệu (Archive) — lưu ý quan trọng

Tính năng **Lưu trữ dữ liệu** sẽ:

- Sao chép dữ liệu xe đã xuất theo khoảng thời gian sang file archive trong thư mục `archives/`.
- Sau đó **xóa vĩnh viễn** các bản ghi tương ứng khỏi CSDL chính.

Khuyến nghị:

- Thực hiện lưu trữ ngoài giờ làm việc.
- Sao lưu file DB trước khi lưu trữ nếu cần.

## 6) Xử lý lỗi thường gặp (Troubleshooting)

- **Không import được Excel / báo thiếu cột**: kiểm tra file có cột bắt buộc (VIN/Chủ hàng/Loại xe) và tiêu đề cột không bị gộp ô.
- **Không thêm được VIN**: VIN có thể đã tồn tại trong bãi hoặc đang ở trạng thái không hợp lệ; hãy tra cứu trong tab **🔍 Tra cứu**.
- **Không tạo được phiếu**: kiểm tra đã chọn đủ **Tài xế** và **Xe vận chuyển**.
- **Báo cáo trống**: thử mở rộng khoảng thời gian hoặc kiểm tra dữ liệu trong bãi.
