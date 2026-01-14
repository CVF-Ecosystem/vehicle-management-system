
# ROADMAP (Canonical)

> **Trạng thái:** ✅ Production Ready (V5.3.0 - All Features Complete)
>
> **Lưu ý cho người dùng cuối:**
>
> - Đây là bản chính thức dành cho nhân viên, người dùng cuối (chạy file .exe, không cần thao tác kỹ thuật)
> - Tất cả các chức năng Phase 1, 2, 3 & 4 đã hoàn thiện, kiểm thử và sẵn sàng sử dụng
> - Nếu cần hướng dẫn sử dụng, nhấn F1 trong ứng dụng hoặc xem file User_Guide.md

Tài liệu này là **nguồn duy nhất** để theo dõi **lộ trình + tiến độ** và cũng là **hướng dẫn vận hành** (để không cần nhiều file).

Mô hình mục tiêu: **Local tại bãi (offline)** + **HQ tổng hợp offline**.

Trạng thái ký hiệu:

- ✅ Done: đã xong, đang dùng ổn định.
- 🚧 In progress: đã có nền tảng, còn phần tiếp theo.
- ⏭ Next: chưa triển khai.

---

## 1) Mục tiêu & phạm vi

- Mỗi bãi vận hành độc lập (SQLite local), **không yêu cầu realtime**.
- HQ tổng hợp báo cáo theo lịch (ngày/tuần) bằng cách nhận file export từ các bãi.
- Xe có thể **chuyển bãi/kho** là nghiệp vụ bình thường.

### Dữ liệu & phân tách DB

- DB xe (local): theo `DB_FILE` trong `config.py`.
- DB bảo mật/audit (tách riêng): `config/security.db` theo `SECURITY_DB_FILE`/`AUDIT_DB_FILE` trong `config.py`.

---

## 2) Cài đặt & chạy ứng dụng

### Yêu cầu môi trường

- Windows
- Python 3.11+
- Có quyền ghi file trong thư mục dự án (để tạo DB/logs/archives)

### Cài đặt

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Chạy

```bash
python main.py
```

---

## 3) Hướng dẫn sử dụng (tóm tắt theo luồng)

### 3.1 Đăng nhập & phân quyền

- Khi mở app sẽ có màn hình đăng nhập.
- Tài khoản mặc định:
  - Username: `admin`
  - Password: `admin123`
- Khuyến nghị: đổi mật khẩu admin ngay sau lần đăng nhập đầu tiên.

### 3.2 Luồng nghiệp vụ chính

- Nhập bãi:
  - Nhập thủ công hoặc import Excel.
  - Có thể chọn vị trí hoặc để hệ thống tự gán vị trí trống.
- Xuất bãi:
  - Xuất theo phiếu (Dispatch, nhiều xe) hoặc xuất lẻ.
- Tồn bãi:
  - Xem/lọc/tìm kiếm, thao tác chỉnh sửa/đổi vị trí/xóa (soft delete) theo quyền.
- Tra cứu:
  - Ưu tiên tra theo VIN (VIN override các filter khác khi có).

### 3.3 Bản đồ bãi, thông báo, phím tắt

- Bản đồ bãi: xem slot trống/có xe, click để xem chi tiết, có zoom và filter.
- Thông báo: xe tồn lâu, bãi sắp đầy, thông báo hệ thống.
- Phím tắt (phổ biến): F5 refresh, Ctrl+N nhập bãi, Ctrl+F tra cứu, Ctrl+D dispatch, Ctrl+Q logout.

---

## 4) Tổng hợp nhiều bãi tại HQ (offline) — Snapshot Bundles (✅ đang dùng)

Mỗi bãi xuất 1 file bundle `.json` theo kỳ (ngày/tuần). HQ import các bundle này vào DB tổng để xuất báo cáo.

### 4.1 Bãi: xuất snapshot bundle

```bash
python tools/export_site_bundle.py --from 2025-01-01 --to 2025-01-07
```

Output mặc định: `exports/bundle_<site_code>_<from>_<to>.json`

### 4.2 HQ: import snapshot bundles

```bash
python tools/import_bundles.py exports/*.json
```

DB tổng mặc định: `config/central_report.db`

Ghi chú: Import idempotent theo `bundle_id` (import lại sẽ tự SKIP).

### 4.3 HQ: xuất báo cáo Excel snapshot

```bash
python tools/generate_central_report.py --from 2025-01-01 --to 2025-01-07
```

Output mặc định: `reports/central_<from>_<to>.xlsx`

---

## 5) Tổng hợp nhiều bãi tại HQ (offline) — Event Bundles (✅ đã có, dùng để đối soát)

Mục đích: tạo “append-only events” từ `audit_logs` để HQ có thể merge idempotent và hỗ trợ đối soát chuyển bãi.

### 5.1 Bãi: xuất event bundle

```bash
python tools/export_site_event_bundle.py --from 2025-01-01 --to 2025-01-07
```

Output mặc định: `exports/events_<site_code>_<from>_<to>.json`

### 5.2 HQ: import event bundles

```bash
python tools/import_event_bundles.py exports/events_*.json
```

DB events mặc định: `config/central_events.db`

Ghi chú: Import idempotent theo `event_uid` (import lại không nhân đôi).

### 5.3 HQ: báo cáo “nghi chuyển bãi” (heuristic)

Heuristic: VIN OUT ở bãi A rồi VIN IN ở bãi B trong N ngày.

```bash
python tools/generate_transfer_report.py --from 2025-01-01 --to 2025-01-07 --max-days 7
```

Output mặc định: `reports/transfers_<from>_<to>.csv`

---

## 6) Testing (khuyến nghị)

```bash
python -m pytest
```

---

## Tiến độ hiện tại (tóm tắt)

| Nhóm | Mục | Trạng thái |
| --- | --- | --- |
| Vận hành local | Nhập/Xuất/Tồn/Tra cứu (VIN ưu tiên) | ✅ |
| Bảo mật | User DB tách riêng + hash password | ✅ |
| Audit | Audit repository + hooks các luồng chính | ✅ |
| HQ offline (snapshot) | Export bundle snapshot + HQ import + Excel report | ✅ |
| HQ offline (events) | Event bundle (từ audit) + HQ import idempotent | ✅ |
| Transfer liên bãi | Report “nghi chuyển bãi” (heuristic) | ✅ |
| UX nâng cao | Progress bar import, Confirm dialog, Auto-save draft | ✅ |
| UX nâng cao | Timeline xe, Keyboard shortcuts mở rộng | ✅ |
| Transfer liên bãi | Chuẩn hoá TRANSFER + auto khấu trừ double-count | ⏭ |
| Tự động hoá HQ | Import theo thư mục + scheduler | ⏭ |

## Giai đoạn 0 — Nền tảng vận hành (✅ Done)

- UI/Tra cứu: ưu tiên tìm theo VIN (VIN override các filter khác khi nhập).
- Security DB tách riêng (users + audit) khỏi DB xe.
- Password hashing (bcrypt) + hỗ trợ verify legacy.
- Export bundle snapshot theo kỳ từ bãi.
- HQ import bundle snapshot vào `central_report.db` (idempotent theo `bundle_id`).
- HQ xuất báo cáo Excel theo kỳ:
  - Tổng kỳ (Nhập/Xuất/Tồn cuối kỳ)
  - Theo bãi
  - Theo chủ hàng/đại lý

## Giai đoạn 1 — Củng cố audit (✅ Done)

- Bổ sung audit hooks cho các luồng quan trọng (best-effort, không làm hỏng nghiệp vụ):
  - Import Excel, Export Excel
  - Tạo/hủy/hoàn tất phiếu (dispatch), xuất theo phiếu, xuất lẻ
  - Xóa/ẩn, restore, archive
  - Backup/restore DB
- Payload audit tối thiểu có thể truy vết: `record_id` (VIN/ID), old → new, và `details` khi cần.

## Giai đoạn 2 — Transfer liên bãi qua “append-only events” (✅ Done)

Định hướng: **không phá luồng snapshot bundle hiện tại**; event pipeline là “cộng thêm” để phục vụ đối soát chuyển bãi.

- ✅ Mỗi site có định danh ổn định `site_instance_id` (tránh trùng khi clone máy/bãi).
- ✅ Export event bundle (từ `audit_logs`) theo khoảng thời gian.
- ✅ HQ import event bundle vào `central_events.db` theo cơ chế idempotent (không nhân đôi theo `event_uid`).
- ✅ Báo cáo “nghi chuyển bãi” (heuristic): VIN OUT ở bãi A rồi VIN IN ở bãi B trong N ngày.

- ⏭ Chuẩn hóa sự kiện TRANSFER (hoặc rule liên kết OUT/IN) để phản ánh chuyển bãi một cách chính xác.
- ⏭ Quy tắc merge/xung đột khi cùng VIN xuất hiện ở nhiều bãi (ưu tiên theo timeline + nguồn).
- ⏭ Tích hợp “khấu trừ chuyển bãi” vào báo cáo HQ (tránh double-count) theo cấu hình bật/tắt.

## Mốc triển khai đề xuất (thứ tự làm)

1) ⏭ Chuẩn hóa TRANSFER (định nghĩa chuẩn, test dataset, rule khớp OUT↔IN)

2) ⏭ Report HQ “đã khấu trừ chuyển bãi” (bật/tắt bằng config để không phá báo cáo snapshot đang dùng)

3) ⏭ Tự động hoá HQ (import folder + Task Scheduler)

4) ⏭ UX: đưa các tool (export/import/report) vào UI

## Giai đoạn 3 — UX Enhancements (✅ Done)

- ✅ Progress bar cho Import Excel (hiển thị tiến độ khi import file lớn)
- ✅ Confirm dialog trước khi xuất xe (hiển thị thông tin xe, chủ hàng, tài xế)
- ✅ Auto-save draft khi nhập xe (tự động lưu bản nháp, khôi phục khi mở lại)
- ✅ Vehicle Timeline (double-click để xem lịch sử hoạt động của xe)
- ✅ Keyboard shortcuts mở rộng (Ctrl+O xuất lẻ, Ctrl+T tồn bãi, F1 trợ giúp)
- ✅ Dashboard auto-refresh (tự động làm mới theo khoảng thời gian)

## Giai đoạn 4 — Tính năng nâng cao (✅ Done)

**MEDIUM PRIORITY (đã hoàn thành):**
- ✅ PDF Reports - Tạo báo cáo PDF với nhiều loại: tồn kho, nhập xuất, chi tiết toàn bộ
- ✅ Webcam Scanner Enhancements - Hỗ trợ chọn camera, zoom, quét liên tục, nhập thủ công, lịch sử quét
- ✅ Enhanced Keyboard Navigation - Enter (xem lịch sử), Space (toggle select), Delete (xóa)

**LOW PRIORITY (đã hoàn thành):**
- ✅ Dark Mode - Hỗ trợ chế độ Sáng/Tối/Hệ thống
- ✅ Config Export/Import - Xuất/nhập cài đặt ứng dụng, reset về mặc định
- ✅ Keyboard Navigation - Phím tắt toàn cục: F5 (làm mới), Ctrl+N/F/E/D/M/B (các tab), Escape (reset)
- ✅ Onboarding Wizard - Hướng dẫn 8 bước cho người dùng mới, tùy chọn không hiển thị lại
- ✅ Print Templates - Quản lý mẫu in: QR tag, phiếu xuất, báo cáo với xem trước

## Giai đoạn 5 — Tự động hóa HQ (⏭ Next)

- Tool import theo thư mục, tự phát hiện bundle/event mới.
- Lịch chạy (Task Scheduler) để tạo báo cáo ngày/tuần.
- Template báo cáo chuẩn (Excel/PDF) theo yêu cầu lãnh đạo.

## Giai đoạn 6 — Nâng cấp UX nâng cao (⏭ Next)

- Tích hợp nút export bundle + generate central report ngay trong UI (không cần chạy CLI).
- Màn hình quản trị người dùng/audit nâng cao (lọc, export log)
