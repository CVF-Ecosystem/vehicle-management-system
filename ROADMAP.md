
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

---

## Giai đoạn 7 — Đề xuất Nâng cấp Toàn diện (Chuyên gia Phần mềm)

> **Ngày đề xuất:** 2026-02-27
> **Mục tiêu:** Nâng cấp từ "ứng dụng desktop tốt" → "hệ thống phần mềm chuyên nghiệp, bảo trì dài hạn"

### 7.1 · Kiến trúc & Scalability

| Ưu tiên | Đề xuất | Lý do |
|---------|---------|-------|
| 🔴 High | **Tách `main.py` thành nhiều module** — `main.py` hiện có 916 dòng, chứa cả UI logic, event handlers, web dashboard management | God class — khó test, khó maintain |
| 🔴 High | **Dependency Injection Container** — Hiện tại các manager được tạo trực tiếp trong `InventoryApp.__init__()` | Khó mock khi test, coupling cao |
| 🟡 Medium | **Repository Pattern nhất quán** — `VehicleManager` vừa là repository vừa có business logic | Vi phạm Single Responsibility |
| 🟡 Medium | **Event Bus / Observer Pattern** — `on_data_changed()` gọi trực tiếp các tab | Coupling giữa các component |
| 🟢 Low | **Config Management với Pydantic** — Thay `configparser` bằng Pydantic Settings | Type safety, validation tự động |

### 7.2 · Testing & CI/CD

| Ưu tiên | Đề xuất | Lý do |
|---------|---------|-------|
| 🔴 High | **GitHub Actions CI pipeline** — Chạy `pytest` tự động khi push/PR | Hiện tại không có CI |
| 🔴 High | **Test coverage ≥ 70%** — Hiện tại coverage thấp, nhiều business logic chưa có test | Rủi ro regression cao |
| 🟡 Medium | **Integration tests cho toàn bộ luồng** — Nhập → Tồn kho → Xuất → Báo cáo | Chỉ có unit tests riêng lẻ |
| 🟡 Medium | **Property-based testing với Hypothesis** — Cho VIN validation, data normalizer | Phát hiện edge cases tự động |
| 🟢 Low | **Mutation testing với mutmut** — Đánh giá chất lượng test suite | Biết test có thực sự kiểm tra logic không |

### 7.3 · Bảo mật

| Ưu tiên | Đề xuất | Lý do |
|---------|---------|-------|
| 🔴 High | **Xóa `unlock.txt` mechanism** — Cơ chế reset admin qua file text là security hole | Bất kỳ ai có quyền ghi file đều có thể reset admin |
| 🔴 High | **Rate limiting cho login** — Hiện có lockout nhưng không có rate limiting ở tầng network | Brute force vẫn có thể qua nhiều connection |
| 🟡 Medium | **Mã hóa SQLite database** — Dùng SQLCipher hoặc encrypt sensitive fields | Dữ liệu xe/chủ hàng lưu plaintext |
| 🟡 Medium | **Audit log integrity** — Thêm hash chain để phát hiện audit log bị sửa | Audit log hiện có thể bị xóa/sửa |
| 🟢 Low | **2FA cho admin account** — TOTP (Google Authenticator) | Tăng bảo mật tài khoản admin |

### 7.4 · Performance & UX

| Ưu tiên | Đề xuất | Lý do |
|---------|---------|-------|
| 🔴 High | **Virtual scrolling cho Treeview** — Khi có >10.000 xe, UI bị lag | Hiện tại load toàn bộ vào memory |
| 🟡 Medium | **Background sync thread** — Tự động refresh data mỗi N phút | Người dùng phải F5 thủ công |
| 🟡 Medium | **Undo/Redo cho thao tác quan trọng** — Nhập xe, xuất xe, xóa xe | Không thể hoàn tác lỗi nhập liệu |
| 🟡 Medium | **Barcode/QR scanner tích hợp tốt hơn** — Hiện tại camera scanner còn thô | Tăng tốc độ nhập liệu thực tế |
| 🟢 Low | **Dark mode hoàn chỉnh** — Một số widget vẫn dùng màu hardcode | Trải nghiệm không nhất quán |

### 7.5 · Code Quality & Maintainability

| Ưu tiên | Đề xuất | Lý do |
|---------|---------|-------|
| 🔴 High | **Type hints đầy đủ** — Nhiều hàm thiếu type annotations | Khó IDE support, khó refactor |
| 🔴 High | **Docstrings chuẩn Google/NumPy style** — Nhiều hàm thiếu hoặc docstring không đầy đủ | Khó onboard developer mới |
| 🟡 Medium | **Linting với ruff/flake8 + pre-commit hooks** — Tự động enforce code style | Hiện tại không có linting |
| 🟡 Medium | **Tách translations thành file JSON** — `translations.py` hiện là Python dict lớn | Khó cho non-developer thêm ngôn ngữ |
| 🟡 Medium | **Database migration system** — Dùng Alembic hoặc custom migration runner | Hiện tại dùng `_upgrade_table_if_needed()` thủ công |
| 🟢 Low | **Changelog tự động** — Dùng conventional commits + `git-cliff` | Dễ track thay đổi theo version |

### 7.6 · Deployment & Distribution

| Ưu tiên | Đề xuất | Lý do |
|---------|---------|-------|
| 🔴 High | **Auto-update mechanism** — Kiểm tra version mới và tự cập nhật | Hiện tại phải cập nhật thủ công |
| 🟡 Medium | **PyInstaller build pipeline** — Tự động build .exe khi tag release | Hiện tại build thủ công |
| 🟡 Medium | **Installer với NSIS/Inno Setup** — Thay vì chạy .exe trực tiếp | Trải nghiệm cài đặt chuyên nghiệp hơn |
| 🟢 Low | **Docker container cho web dashboard** — Streamlit dashboard có thể chạy độc lập | Dễ deploy lên server HQ |

### 7.7 · Tính năng Nghiệp vụ Còn thiếu

| Ưu tiên | Đề xuất | Lý do |
|---------|---------|-------|
| 🔴 High | **Import/Export từ hệ thống ERP** — Kết nối với SAP/Oracle/Odoo qua API | Tránh nhập liệu 2 lần |
| 🟡 Medium | **Báo cáo tự động qua email** — Gửi báo cáo ngày/tuần tự động | Giảm công việc thủ công cho HQ |
| 🟡 Medium | **Mobile app (React Native/Flutter)** — Scan QR/barcode trực tiếp từ điện thoại | Nhân viên bãi không cần máy tính |
| 🟡 Medium | **Hình ảnh xe** — Chụp ảnh xe khi nhập/xuất, lưu kèm record | Bằng chứng trực quan, giảm tranh chấp |
| 🟢 Low | **GPS tracking tích hợp** — Theo dõi vị trí xe vận chuyển | Biết xe đang ở đâu trong quá trình vận chuyển |

---

### Thứ tự ưu tiên thực hiện (Roadmap 2026)

```
Q1/2026: 7.2 (CI/CD + coverage) + 7.3 (security holes) + 7.5 (type hints + linting)
Q2/2026: 7.1 (refactor main.py) + 7.4 (virtual scrolling) + 7.6 (auto-update)
Q3/2026: 7.7 (ERP integration + email reports) + 7.4 (undo/redo)
Q4/2026: 7.7 (mobile app) + 7.6 (Docker)
```

---

## Giai đoạn CQ — Code Quality Fixes (⏭ Next)

> **Nguồn gốc:** Kết quả đánh giá chất lượng code ngày 2026-02-27.
> Tổng điểm hiện tại: **6.7/10**. Mục tiêu sau khi fix: **8.5/10**.

### CQ-1 · Critical Bugs ✅ Đã fix (2026-02-27)

| ID | File | Vấn đề | Trạng thái |
|----|------|---------|-----------|
| CQ-1.1 | `auth/auth_manager.py` | Dead code `cls._current_user = None` sau `return` | ✅ Đã xóa |
| CQ-1.2 | `auth/auth_manager.py` | Phương thức `get_user_repository()` định nghĩa 2 lần | ✅ Đã hợp nhất (xóa định nghĩa thừa) |
| CQ-1.3 | `report_generators/pdf_generator.py` | 8 lệnh `print()` debug trong production code | ✅ Thay bằng `logging.debug()` |

### CQ-2 · Error Handling ✅ Đã fix (2026-02-27)

| ID | File | Vấn đề | Trạng thái |
|----|------|---------|-----------|
| CQ-2.1 | `main.py` | Bare `except:` khi terminate Streamlit | ✅ Đổi thành `except Exception:` |
| CQ-2.2 | `report_generators/excel_generator.py` | Bare `except: pass` | ✅ Đổi thành `except (TypeError, AttributeError):` |
| CQ-2.3 | `ui/components.py` | Bare `except:` trong UI components | ✅ Đổi thành `except Exception:` |
| CQ-2.4 | `ui/config_dialog.py` | Bare `except: pass` | ✅ Đổi thành `except Exception as e: logging.warning(...)` |
| CQ-2.5 | `ui/deleted_vehicles_dialog.py` | Bare `except:` trong format date | ✅ Đổi thành `except (ValueError, TypeError):` |
| CQ-2.6 | `ui/onboarding_dialog.py` | Bare `except:` | ✅ Đổi thành `except Exception:` |
| CQ-2.7 | `ui/pdf_report_dialog.py` | Bare `except:` | ✅ Đổi thành `except Exception:` / `except ValueError:` |
| CQ-2.8 | `ui/user_management_dialog.py` | Bare `except:` khi parse datetime | ✅ Đổi thành `except (ValueError, TypeError):` |
| CQ-2.9 | `ui/yard_map_tab.py` | Bare `except:` | ✅ Đổi thành `except (ValueError, TypeError):` |

> **Tổng cộng:** 18 chỗ dùng bare `except:` đã được sửa.

### CQ-3 · Code Duplication & Initialization (Ưu tiên trung bình)

| ID | File | Vấn đề | Trạng thái |
|----|------|---------|-----------|
| CQ-3.1 | `main.py` | Font được khởi tạo 2 lần trong `__init__` | ✅ Đã xóa lần khởi tạo đầu (hardcode Arial) |
| CQ-3.2 | `database/vehicle_manager.py` | `from database.audit_repository import ...` nằm trong hàm — import lặp lại | ✅ Chuyển tất cả lên đầu file |
| CQ-3.3 | `main.py` | `on_data_changed()` refresh toàn bộ tất cả tabs | ✅ Chỉ refresh stock_tab khi đang active; dropdowns vẫn update nhẹ |

### CQ-4 · Testing Issues (Ưu tiên trung bình)

| ID | File | Vấn đề | Trạng thái |
|----|------|---------|-----------|
| CQ-4.1 | `tests/conftest.py` | Test data dùng status lowercase `"in_stock"`, `"dispatched"` | ✅ Sửa thành `"IN_STOCK"`, `"SHIPPED"` |
| CQ-4.2 | `tests/test_full_logic.py` | Không phải pytest test chuẩn | ✅ Tạo `tests/test_logic_pytest.py` với pytest classes + assert chuẩn |

### CQ-5 · Robustness & Edge Cases (Ưu tiên thấp)

| ID | File | Vấn đề | Trạng thái |
|----|------|---------|-----------|
| CQ-5.1 | `reporting/central_report.py` | Không có guard khi `bundle_ids` rỗng | ✅ Thêm guard `if not bundle_ids: raise ValueError(...)` |
| CQ-5.2 | `auth/auth_manager.py` | `refresh_session()` không được gọi tự động | ✅ Gọi trong `on_tab_change()` và `on_data_changed()` |
| CQ-5.3 | `main.py` | `time.sleep(3)` cứng nhắc khi chờ Streamlit | ✅ Thay bằng polling loop kiểm tra port (tối đa 10 giây) |
| CQ-5.4 | `config.py` | `APP_VERSION` không theo SemVer | ✅ Đổi thành `"1.0.0"`, thêm `APP_VERSION_DISPLAY` |
| CQ-5.5 | `main.py` | `menu_font = ("Arial", 12)` hardcode font | ✅ Dùng `(FONT_FAMILY, FONT_SIZE_SMALL)` từ `config.py` |

### CQ-6 · Thread Safety (Ưu tiên thấp)

| ID | File | Vấn đề | Trạng thái |
|----|------|---------|-----------|
| CQ-6.1 | `database/user_repository.py` | `check_same_thread=False` nhưng không có mutex | ✅ Thêm `threading.Lock()` bảo vệ create/update/delete/change_password |

---

### Tóm tắt tiến độ (2026-02-27) — ✅ HOÀN THÀNH TẤT CẢ

- **Đã fix:** CQ-1.1, CQ-1.2, CQ-1.3, CQ-2.1~2.9 (18 bare except), CQ-3.1, CQ-3.2, CQ-3.3, CQ-4.1, CQ-4.2, CQ-5.1, CQ-5.2, CQ-5.3, CQ-5.4, CQ-5.5, CQ-6.1
- **Tổng:** 16/16 mục đã hoàn thành

### Tiêu chí hoàn thành

- [x] CQ-1: Không còn dead code, không còn duplicate method
- [x] CQ-2: `grep -r "except:" --include="*.py"` trả về 0 kết quả trong source code (ngoài tests)
- [x] CQ-3.1: `__init__` của `InventoryApp` không còn khởi tạo font 2 lần
- [x] CQ-3.2: Tất cả import audit_repository đã ở đầu file
- [x] CQ-3.3: `on_data_changed()` chỉ refresh stock_tab khi đang active
- [x] CQ-4.1: Test data dùng đúng status constants
- [x] CQ-4.2: `tests/test_logic_pytest.py` với pytest classes + assert chuẩn
- [x] CQ-5.1: `central_report.py` có guard cho `bundle_ids` rỗng
- [x] CQ-5.2: `refresh_session()` được gọi trong `on_tab_change()` và `on_data_changed()`
- [x] CQ-5.3: Polling loop thay `time.sleep(3)` khi chờ Streamlit
- [x] CQ-5.4: `APP_VERSION` theo SemVer (`1.0.0`)
- [x] CQ-5.5: Menu font dùng `FONT_FAMILY` constant
- [x] CQ-6.1: `threading.Lock()` bảo vệ write ops trong `user_repository.py`
