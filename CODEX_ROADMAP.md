# CODEX IMPLEMENTATION ROADMAP
## Vehicle Management System — Lộ trình thi công cho Codex

**Ngày tạo:** 2026-05-22  
**Nguồn gốc:** Kết quả đánh giá EA (CODE_QUALITY_ASSESSMENT.md) + ROADMAP.md hiện hành  
**Mục tiêu:** Nâng ứng dụng từ B → A- về chất lượng, bảo mật và khả năng bảo trì

---

## Hướng dẫn cho Codex

- Mỗi task là **độc lập** và có thể thi công theo thứ tự từ trên xuống.
- Mỗi task có **Acceptance Criteria** rõ ràng — hoàn thành khi tất cả criteria được đáp ứng.
- **Không** refactor code nằm ngoài phạm vi của task đang làm.
- **Không** thay đổi logic nghiệp vụ khi không được yêu cầu — chỉ sửa đúng vấn đề được chỉ định.
- Sau mỗi task, chạy `python -m pytest` để đảm bảo không có regression.
- Ký hiệu độ phức tạp: **S** (< 1h) | **M** (1–4h) | **L** (4–8h) | **XL** (> 8h)

---

## PHASE 1 — BẢO MẬT CỐT LÕI (Critical Security)

### TASK-SEC-01 · Bắt buộc đổi mật khẩu admin lần đầu đăng nhập
**Độ phức tạp:** M | **Ưu tiên:** CRITICAL

**Bối cảnh:** Default password `admin123` được hardcode trong `database/user_repository.py`. Hiện tại không có cơ chế nào bắt buộc user đổi mật khẩu sau lần đăng nhập đầu tiên.

**Files cần sửa:**
- `database/user_repository.py` — thêm cột `must_change_password` vào bảng `users`
- `auth/auth_manager.py` — sau `login()` thành công, kiểm tra flag và trả về trạng thái
- `ui/login_dialog.py` — nếu flag = True, hiển thị dialog đổi mật khẩu ngay; không cho qua
- `ui/components.py` hoặc tạo `ui/change_password_dialog.py` — dialog đổi mật khẩu bắt buộc

**Chi tiết thực hiện:**
1. Migration schema: thêm `must_change_password INTEGER NOT NULL DEFAULT 0` vào bảng `users`.
2. Khi tạo user admin lần đầu (hoặc khi mật khẩu là `admin123`), set `must_change_password = 1`.
3. Sau `auth_manager.login()` thành công, nếu `must_change_password = 1`:
   - Trả về `LoginResult.MUST_CHANGE_PASSWORD` thay vì `LoginResult.SUCCESS`.
   - Hiển thị dialog đổi mật khẩu full-screen (không có nút Cancel/Đóng).
   - Chỉ cho phép tiếp tục sau khi đổi thành công.
4. Validation mật khẩu mới: tối thiểu 8 ký tự, có chữ hoa + chữ thường + số.
5. Sau khi đổi, set `must_change_password = 0`.

**Acceptance Criteria:**
- [ ] Login với `admin/admin123` → hiện dialog đổi mật khẩu, không vào được main UI.
- [ ] Nhấn X hoặc Escape không đóng được dialog đổi mật khẩu.
- [ ] Mật khẩu < 8 ký tự → hiện error message, không cho lưu.
- [ ] Sau khi đổi thành công → vào được main UI bình thường.
- [ ] Login lần 2 với mật khẩu mới → không hiện dialog đổi mật khẩu.
- [ ] `python -m pytest tests/test_auth.py` pass toàn bộ.

---

### TASK-SEC-02 · Thêm xác thực cho Flask dashboard API
**Độ phức tạp:** M | **Ưu tiên:** CRITICAL

**Bối cảnh:** `dashboard_api.py` chạy Flask server phục vụ `dashboard.html` mà không có bất kỳ xác thực nào. Bất kỳ ai có thể truy cập `http://localhost:PORT` đều xem được toàn bộ dữ liệu.

**Files cần sửa:**
- `dashboard_api.py` — thêm token-based auth cho tất cả API endpoints
- `ui/web_dashboard_manager.py` — generate và truyền token cho dashboard
- `dashboard.html` — include token trong API calls (header `Authorization`)

**Chi tiết thực hiện:**
1. Khi Flask server khởi động, generate một `session_token` ngẫu nhiên (`secrets.token_urlsafe(32)`).
2. Tất cả API endpoints kiểm tra header `Authorization: Bearer <token>`.
3. Nếu thiếu hoặc sai token → trả về HTTP 401.
4. Token được truyền vào dashboard qua URL parameter khi mở browser (ví dụ: `http://localhost:8502?token=xxx`).
5. `dashboard.html` lưu token vào JS variable và include trong mọi fetch() call.
6. Thêm CORS header chỉ cho phép `localhost` (không wildcard).

**Acceptance Criteria:**
- [ ] `curl http://localhost:8502/api/vehicles` → 401 Unauthorized.
- [ ] `curl -H "Authorization: Bearer <valid_token>" http://localhost:8502/api/vehicles` → 200 OK.
- [ ] Mở dashboard từ app → load bình thường.
- [ ] Token mới được tạo mỗi lần app khởi động.

---

### TASK-SEC-03 · Bật SQLite Foreign Key Constraints
**Độ phức tạp:** S | **Ưu tiên:** HIGH

**Bối cảnh:** SQLite mặc định tắt foreign key enforcement. Hiện tại có thể tạo dispatch record với `driver_id` không tồn tại mà không có lỗi.

**Files cần sửa:**
- `database/base_manager.py` — thêm PRAGMA sau khi mở connection

**Chi tiết thực hiện:**
1. Trong method `_get_connection()` hoặc `_initialize_connection()`, thêm ngay sau khi tạo connection:
   ```python
   conn.execute("PRAGMA foreign_keys = ON")
   ```
2. Thêm test xác nhận FK đang hoạt động.

**Acceptance Criteria:**
- [ ] `PRAGMA foreign_keys` query trả về `1`.
- [ ] Thử INSERT dispatch với `driver_id` không tồn tại → raise `sqlite3.IntegrityError`.
- [ ] Tất cả test hiện tại vẫn pass (không có cascade delete bất ngờ).
- [ ] Test mới `tests/test_foreign_keys.py` kiểm tra FK constraint trên các bảng chính.

---

### TASK-SEC-04 · Transactional Excel Import
**Độ phức tạp:** M | **Ưu tiên:** HIGH

**Bối cảnh:** `excel_importer.py` import từng xe một mà không có database transaction. Nếu lỗi ở xe thứ 150/200, 149 xe đầu đã được commit vào DB — tạo ra trạng thái dữ liệu không nhất quán.

**Files cần sửa:**
- `excel_importer.py` — wrap toàn bộ import loop trong transaction; validate VIN trước khi insert

**Chi tiết thực hiện:**
1. Trước vòng lặp insert, collect toàn bộ VINs cần import.
2. Query DB một lần để kiểm tra các VIN nào đã tồn tại → báo lỗi sớm (fail-fast).
3. Wrap vòng lặp insert trong `conn.execute("BEGIN")` / `conn.execute("COMMIT")`.
4. Trong except: `conn.execute("ROLLBACK")` và re-raise exception với thông tin row bị lỗi.
5. Progress callback: bắt exception trong callback và log thay vì swallow.

**Acceptance Criteria:**
- [ ] Import file Excel với VIN trùng ở row cuối → không có xe nào được import, DB giữ nguyên.
- [ ] Import file Excel hợp lệ → tất cả xe được import trong một transaction.
- [ ] Progress callback lỗi → log warning, không crash import.
- [ ] Test mới `tests/test_excel_importer.py::test_partial_import_rollback` pass.

---

## PHASE 2 — HIỆU NĂNG VÀ UX (Performance & UX) ✅ COMPLETED (22/05/2026)

### TASK-PERF-01 · Phân trang cho Stock Tab ✅ DONE
**Độ phức tạp:** M | **Ưu tiên:** HIGH

**Bối cảnh:** `ui/stock_tab.py` fetch toàn bộ xe vào `Treeview` mà không có phân trang. Với 1000+ xe, UI bị lag khi load.

**Files cần sửa:**
- `ui/stock_tab.py` — implement lazy loading với pagination
- `database/vehicle_manager.py` — thêm method `get_vehicles_paginated(offset, limit, filters)`

**Chi tiết thực hiện:**
1. Thêm `get_vehicles_paginated(offset: int, limit: int = 100, **filters) -> tuple[list, int]` vào `VehicleManager` — trả về (rows, total_count).
2. `stock_tab.py`: mặc định load 100 xe đầu tiên.
3. Thêm thanh pagination ở cuối tab: `[< Trước] [Trang 1/5] [Tiếp >]` hoặc nút "Tải thêm 100 xe".
4. Khi search/filter thay đổi → reset về trang 1.
5. Hiển thị label: "Đang hiển thị 1–100 / 847 xe".

**Acceptance Criteria:**
- [x] Với 500 xe trong DB, stock tab load trong < 1s.
- [x] Nút "Trang tiếp" → load 100 xe tiếp theo đúng.
- [x] Filter/search reset về trang 1.
- [x] Label hiển thị đúng tổng số và range đang xem.
- [x] `python -m pytest tests/ -m "not ui"` pass toàn bộ.

---

### TASK-PERF-02 · Background Thread cho Owner Normalization ✅ DONE
**Độ phức tạp:** L | **Ưu tiên:** HIGH

**Bối cảnh:** `VehicleManager.__init__()` gọi `_normalize_all_existing_owners()` synchronously — đây là O(n²) phonetic matching có thể mất 5–30 giây với dataset lớn, blocking main thread trong khi app khởi động.

**Files cần sửa:**
- `database/vehicle_manager.py` — chuyển normalization sang background thread
- `main.py` — hiển thị loading indicator trong khi normalization chạy

**Chi tiết thực hiện:**
1. Trong `VehicleManager.__init__()`, không gọi `_normalize_all_existing_owners()` ngay.
2. Thêm method `start_background_normalization(callback=None)` — chạy trong `threading.Thread(daemon=True)`.
3. Kết quả normalization được cache vào file `config/owner_normalization_cache.json` (keyed by VIN+owner hash).
4. Lần khởi động kế tiếp: load cache trước, chỉ normalize những VIN mới chưa có trong cache.
5. `main.py`: hiển thị status bar message "Đang chuẩn hóa dữ liệu chủ hàng..." trong khi thread chạy.
6. Thread hoàn thành → gọi callback để refresh dropdown chủ hàng.

**Acceptance Criteria:**
- [x] App khởi động và hiển thị UI trong < 3s (không phụ thuộc số xe).
- [x] Status bar hiển thị progress normalization.
- [x] Normalization hoàn thành trong background, dropdown được update.
- [x] Lần 2 khởi động với cùng data: cache hit, không chạy lại normalization.
- [ ] Thêm xe mới → chỉ normalize xe đó, không chạy lại toàn bộ. *(cache hash-based, cả bảng vẫn re-scan — toàn bộ đã được normalize)*

---

### TASK-PERF-03 · Gộp hai Dashboard thành một ✅ DONE
**Độ phức tạp:** L | **Ưu tiên:** MEDIUM

**Bối cảnh:** Có hai implementation dashboard song song: `web_dashboard.py` (Streamlit) và `dashboard_api.py` (Flask). Cả hai implement cùng SQL queries, tạo maintenance debt khi query cần thay đổi.

**Files cần sửa:**
- Giữ lại `dashboard_api.py` (Flask — nhẹ hơn, không cần Streamlit)
- Cải thiện `dashboard.html` với charts từ Chart.js (thay thế Streamlit)
- Xóa `web_dashboard.py` sau khi migrated
- `ui/web_dashboard_manager.py` — chỉ quản lý Flask server
- `config.py` — xóa constants liên quan Streamlit

**Chi tiết thực hiện:**
1. Thêm vào `dashboard_api.py` các endpoints còn thiếu so với Streamlit version:
   - `/api/stats/by_owner` — thống kê theo chủ hàng
   - `/api/stats/trends` — xu hướng nhập/xuất theo ngày
   - `/api/vehicles/aging` — xe tồn lâu
2. Cập nhật `dashboard.html` dùng Chart.js (CDN) để render charts từ JSON API.
3. Test Flask dashboard đầy đủ tính năng.
4. Xóa `web_dashboard.py` và dependencies Streamlit trong `requirements.txt`.
5. Cập nhật `web_dashboard_manager.py` chỉ còn khởi động Flask.

**Acceptance Criteria:**
- [x] Flask dashboard hiển thị đầy đủ: tồn kho, thống kê chủ hàng, trends, aging *(React+Recharts, tốt hơn Chart.js)*.
- [x] `web_dashboard.py` và imports Streamlit đã xóa.
- [x] `requirements.txt` không còn `streamlit`.
- [x] `pip install -r requirements.txt` thành công.

---

## PHASE 3 — CHẤT LƯỢNG CODE (Code Quality)

### TASK-CQ-01 · Thêm Type Hints cho Manager và Repository Classes
**Độ phức tạp:** L | **Ưu tiên:** MEDIUM

**Bối cảnh:** Hầu hết các method trong manager/repository classes thiếu type annotations, giảm IDE support và tăng rủi ro khi refactor.

**Files cần sửa (theo thứ tự ưu tiên):**
1. `database/vehicle_manager.py`
2. `database/dispatch_manager.py`
3. `database/entity_manager.py`
4. `database/user_repository.py`
5. `database/audit_repository.py`
6. `auth/auth_manager.py`
7. `core/backup_service.py`

**Chi tiết thực hiện:**
1. Thêm type hints cho tất cả method signatures (parameters + return types).
2. Dùng `from __future__ import annotations` ở đầu file (Python 3.11 compatible).
3. Dùng `from typing import Optional, Union` cho các trường hợp nullable.
4. Dùng TypedDict hoặc dataclass cho các dict return phức tạp.
5. Chạy `mypy --strict` và fix các lỗi type error tìm được.

**Acceptance Criteria:**
- [ ] Tất cả public methods trong 7 files trên có đầy đủ type annotations.
- [ ] `mypy database/ auth/ core/ --ignore-missing-imports` trả về 0 errors.
- [ ] Không thay đổi logic nghiệp vụ (chỉ thêm annotations).

---

### TASK-CQ-02 · Fix Dependencies trong requirements.txt ✅ DONE
**Độ phức tạp:** S | **Ưu tiên:** MEDIUM

**Bối cảnh:** `cryptography` thiếu trong `requirements.txt`. `thefuzz` trùng lặp với `RapidFuzz`. Port 8502 hardcode ở nhiều nơi.

**Files cần sửa:**
- `requirements.txt`
- `config.py`
- `dashboard_api.py`
- `ui/web_dashboard_manager.py`

**Chi tiết thực hiện:**
1. Thêm `cryptography>=41.0.0` vào `requirements.txt`.
2. Xóa `thefuzz` khỏi `requirements.txt` (RapidFuzz là drop-in replacement nhanh hơn).
3. Tìm và thay tất cả `from thefuzz import` → `from rapidfuzz import` trong codebase.
4. Thêm `DASHBOARD_PORT: int = 8502` vào `config.py`.
5. Thay thế hardcode `8502` trong `dashboard_api.py` và `web_dashboard_manager.py` bằng `config.DASHBOARD_PORT`.

**Acceptance Criteria:**
- [x] `pip install -r requirements.txt` thành công, không missing dependency.
- [x] `grep -r "thefuzz" --include="*.py"` trả về 0 kết quả.
- [x] `grep -r "8502" --include="*.py"` trả về 0 kết quả *(web_dashboard_manager.py dùng `config.DASHBOARD_PORT`)*.
- [x] Fuzzy matching vẫn hoạt động bình thường.

---

### TASK-CQ-03 · Audit Log Purging Strategy
**Độ phức tạp:** M | **Ưu tiên:** MEDIUM

**Bối cảnh:** `audit_repository.py` chỉ append, không có cơ chế xóa log cũ. DB sẽ tăng trưởng vô hạn.

**Files cần sửa:**
- `database/audit_repository.py` — thêm method purge
- `config.py` — thêm constant `AUDIT_LOG_RETENTION_DAYS`
- `core/backup_service.py` — gọi purge khi tạo backup (tùy chọn)
- `ui/user_management_dialog.py` hoặc menu — expose nút "Dọn dẹp audit log"

**Chi tiết thực hiện:**
1. Thêm `AUDIT_LOG_RETENTION_DAYS: int = 365` vào `config.py`.
2. Thêm method `archive_old_logs(before_days: int) -> int` vào `AuditRepository`:
   - Di chuyển logs cũ hơn `before_days` vào bảng `audit_logs_archive` (tạo nếu chưa có, cùng schema).
   - Trả về số records được archive.
3. Thêm method `get_log_stats() -> dict` trả về: total_records, oldest_record, newest_record, size_estimate.
4. Trong menu Admin hoặc backup dialog: thêm nút "Dọn dẹp log cũ" gọi `archive_old_logs(AUDIT_LOG_RETENTION_DAYS)`.
5. Tùy chọn: tự động gọi `archive_old_logs` sau khi tạo backup thành công.

**Acceptance Criteria:**
- [ ] `archive_old_logs(30)` di chuyển đúng records > 30 ngày tuổi sang `audit_logs_archive`.
- [ ] Records trong 30 ngày gần đây không bị ảnh hưởng.
- [ ] Idempotent: chạy 2 lần không duplicate records trong archive.
- [ ] Test `tests/test_audit_repository.py::test_purge_old_logs` pass.

---

### TASK-CQ-04 · Schema Versioning và Migration System
**Độ phức tạp:** M | **Ưu tiên:** MEDIUM

**Bối cảnh:** `base_manager.py` dùng `_upgrade_table_if_needed()` thủ công, không có version tracking. Không thể biết DB đang ở schema version nào.

**Files cần sửa:**
- `database/base_manager.py` — thêm bảng `_schema_meta` và migration runner
- Tạo `database/migrations/` — thư mục chứa migration scripts

**Chi tiết thực hiện:**
1. Tạo bảng `_schema_meta (key TEXT PRIMARY KEY, value TEXT)` nếu chưa có.
2. Ghi `schema_version = "1"` khi tạo DB lần đầu.
3. Tạo `database/migrations/migration_runner.py` với:
   ```python
   MIGRATIONS = {
       "1": migrate_v1_to_v2,  # thêm must_change_password
       "2": migrate_v2_to_v3,  # thêm audit_logs_archive
   }
   ```
4. Khi app khởi động: đọc version hiện tại, chạy các migration còn thiếu theo thứ tự.
5. Mỗi migration chạy trong transaction — rollback nếu lỗi.
6. Chuyển các `ALTER TABLE` trong `_upgrade_table_if_needed()` thành migration scripts.

**Acceptance Criteria:**
- [ ] DB mới tạo có bảng `_schema_meta` với `schema_version` đúng version mới nhất.
- [ ] DB cũ (version 0) được tự động migrate lên version mới nhất khi app khởi động.
- [ ] Migration lỗi → rollback, app hiển thị error message rõ ràng.
- [ ] `python -m pytest tests/test_database.py` pass toàn bộ.

---

### TASK-CQ-05 · Refactor main.py — Tách Controller Classes
**Độ phức tạp:** XL | **Ưu tiên:** MEDIUM

**Bối cảnh:** `main.py` hiện 808 dòng, chứa: app initialization, menu building, tab management, event handling, web dashboard management, session management, và business logic calls. Vi phạm Single Responsibility.

**Files cần tạo/sửa:**
- `ui/app_controller.py` — class `AppController`: quản lý app lifecycle, session, menu
- `ui/tab_manager.py` — class `TabManager`: quản lý tab switching, refresh, lazy loading
- `ui/web_dashboard_manager.py` — đã có, cải thiện interface
- `main.py` — chỉ còn: import, parse args, khởi tạo AppController, `app.mainloop()`

**Chi tiết thực hiện:**
1. Tạo `AppController(ctk.CTk)` — chứa: `__init__`, `_build_menu`, `_build_status_bar`, `on_close`, keyboard shortcuts.
2. Tạo `TabManager` — chứa: `add_tab`, `switch_to`, `refresh_active`, `refresh_all_dropdowns`, `on_data_changed`.
3. Chuyển `WebDashboardManager` logic từ `main.py` vào `web_dashboard_manager.py` (đã có, chuẩn hóa interface).
4. `main.py` sau refactor:
   ```python
   from ui.app_controller import AppController
   if __name__ == "__main__":
       app = AppController()
       app.mainloop()
   ```
5. Đảm bảo tất cả keyboard shortcuts vẫn hoạt động sau refactor.

**Acceptance Criteria:**
- [ ] `main.py` dưới 50 dòng sau refactor.
- [ ] Tất cả tính năng hiện tại vẫn hoạt động bình thường.
- [ ] `python -m pytest` pass toàn bộ.
- [ ] Không có circular import mới.
- [ ] Keyboard shortcuts (F5, Ctrl+N, Ctrl+F, v.v.) vẫn hoạt động.

---

## PHASE 4 — TESTING VÀ CI/CD

### TASK-TEST-01 · Tăng Test Coverage lên 70%
**Độ phức tạp:** XL | **Ưu tiên:** HIGH

**Bối cảnh:** Coverage hiện tại ước tính ~40–50%. Các path chưa có test: excel importer, notification service, dashboard API, report generators.

**Files cần tạo:**
- `tests/test_excel_importer.py` — import thành công, rollback khi lỗi, VIN trùng
- `tests/test_notification_service.py` — aging check, yard full, low stock
- `tests/test_dashboard_api.py` — API endpoints, authentication
- `tests/test_report_generators.py` — PDF, Excel, Word output
- `tests/test_backup_encryption.py` — encrypt/decrypt, verify checksum

**Chi tiết thực hiện:**
Mỗi test file phải cover:
1. **Happy path** — input hợp lệ, output đúng.
2. **Error path** — input lỗi, exception đúng loại.
3. **Edge case** — empty input, boundary values, Vietnamese characters.

Dùng fixtures từ `conftest.py` (`force_test_db`, `sample_db`). Không mock database (dùng real SQLite in-memory).

Chạy coverage report:
```bash
python -m pytest --cov=. --cov-report=html --cov-report=term-missing
```

**Acceptance Criteria:**
- [ ] `pytest --cov` báo cáo overall coverage ≥ 70%.
- [ ] `excel_importer.py` coverage ≥ 80%.
- [ ] `notification_service.py` coverage ≥ 70%.
- [ ] `dashboard_api.py` coverage ≥ 60%.
- [ ] Không có test nào depend vào production DB (bảo vệ bởi `protect_production_db` fixture).

---

### TASK-TEST-02 · GitHub Actions CI Pipeline
**Độ phức tạp:** M | **Ưu tiên:** HIGH

**Bối cảnh:** Hiện tại không có CI — không ai biết khi nào tests fail sau một commit.

**Files cần tạo:**
- `.github/workflows/ci.yml`

**Chi tiết thực hiện:**
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov mypy
      - run: python -m pytest --cov --cov-report=term-missing -q
      - run: mypy database/ auth/ core/ --ignore-missing-imports
```

**Acceptance Criteria:**
- [ ] Push lên GitHub → CI chạy tự động.
- [ ] Test fail → CI fail với exit code non-zero.
- [ ] Coverage report được hiển thị trong CI output.
- [ ] mypy check chạy trong CI.

---

## PHASE 5 — TÍNH NĂNG NGHIỆP VỤ CÒN THIẾU (Business Features)

### TASK-BIZ-01 · Chuẩn hóa TRANSFER liên bãi
**Độ phức tạp:** XL | **Ưu tiên:** HIGH

**Bối cảnh:** Từ `ROADMAP.md` phần ⏭ Next: "Chuẩn hóa sự kiện TRANSFER (hoặc rule liên kết OUT/IN) để phản ánh chuyển bãi một cách chính xác." Hiện tại heuristic dựa trên VIN OUT ở bãi A rồi VIN IN ở bãi B trong N ngày.

**Files cần sửa/tạo:**
- `database/base_manager.py` — thêm bảng `transfer_links`
- `tools/generate_transfer_report.py` — cải thiện heuristic thành rule-based
- `reporting/transfer_report.py` — tạo mới
- `tools/import_event_bundles.py` — thêm logic link OUT→IN events

**Chi tiết thực hiện:**
1. Định nghĩa event `TRANSFER`: khi import event bundle, nếu VIN OUT ở site A và VIN IN ở site B trong 7 ngày → tạo `transfer_link` record.
2. Bảng `transfer_links (id, vin, from_site, to_site, out_event_uid, in_event_uid, transfer_date, confidence)`.
3. Confidence score: 1.0 nếu OUT và IN liền nhau không có event khác; thấp hơn nếu có gap.
4. Rule cấu hình trong `config.py`: `TRANSFER_MAX_DAYS = 7`, `TRANSFER_MIN_CONFIDENCE = 0.8`.
5. Báo cáo HQ: phân biệt "xe thực nhập" vs "xe chuyển từ bãi khác" để tránh double-count.
6. Config bật/tắt: `DEDUCT_TRANSFERS_FROM_HQ_REPORT = True/False`.

**Acceptance Criteria:**
- [ ] Import 2 event bundles: bãi A xuất VIN123, bãi B nhập VIN123 cùng ngày → tạo transfer_link.
- [ ] Báo cáo HQ với `DEDUCT_TRANSFERS_FROM_HQ_REPORT = True` không double-count VIN123.
- [ ] Báo cáo HQ với `DEDUCT_TRANSFERS_FROM_HQ_REPORT = False` giữ nguyên hành vi cũ.
- [ ] `tools/generate_transfer_report.py --help` hiển thị options.

---

### TASK-BIZ-02 · HQ Automation — Import theo thư mục + Scheduler
**Độ phức tạp:** L | **Ưu tiên:** HIGH

**Bối cảnh:** Từ `ROADMAP.md` Giai đoạn 5 ⏭: "Tool import theo thư mục, tự phát hiện bundle/event mới. Lịch chạy (Task Scheduler) để tạo báo cáo ngày/tuần."

**Files cần sửa/tạo:**
- `tools/hq_automation.py` — đã có nền tảng, cần hoàn thiện
- `tools/folder_watcher.py` — tạo mới: watch thư mục exports/
- Tạo `scripts/setup_task_scheduler.ps1` — tự động tạo Windows Task Scheduler job

**Chi tiết thực hiện:**
1. `folder_watcher.py`:
   - Dùng `watchdog` library để watch thư mục `AUTOMATION_MONITOR_FOLDER`.
   - Phát hiện file `bundle_*.json` hoặc `events_*.json` mới.
   - Tự động gọi `import_bundles.py` hoặc `import_event_bundles.py`.
   - Log kết quả vào `logs/hq_automation.log`.
2. `hq_automation.py` chế độ `--daemon`: chạy liên tục, watch thư mục.
3. `hq_automation.py` chế độ `--once`: import tất cả file mới + generate report, rồi exit (dùng với Task Scheduler).
4. `scripts/setup_task_scheduler.ps1`: tạo Windows Task Scheduler job chạy `--once` hàng ngày lúc 7:00 SA.

**Acceptance Criteria:**
- [ ] Copy file bundle mới vào thư mục watched → tự động import trong < 30s.
- [ ] Import idempotent: copy lại file đã import → SKIP, không import lần 2.
- [ ] `--once` mode: import xong, generate Excel report, exit 0.
- [ ] `scripts/setup_task_scheduler.ps1` tạo Task Scheduler job thành công.

---

### TASK-BIZ-03 · Tích hợp công cụ HQ vào UI
**Độ phức tạp:** L | **Ưu tiên:** MEDIUM

**Bối cảnh:** Từ `ROADMAP.md` Giai đoạn 6 ⏭: "Tích hợp nút export bundle + generate central report ngay trong UI (không cần chạy CLI)."

**Files cần sửa/tạo:**
- `ui/hq_tools_dialog.py` — tạo mới: dialog quản lý HQ tools
- `main.py` (hoặc `app_controller.py` sau TASK-CQ-05) — thêm menu item "HQ Tools"
- `tools/export_site_bundle.py` — expose as importable function (không chỉ CLI)

**Chi tiết thực hiện:**
1. Dialog "HQ Tools" có 3 tab:
   - **Export Bundle**: chọn date range → export `bundle_*.json` → hiện status.
   - **Import Bundles**: chọn file(s) JSON → import → hiển thị kết quả (đã import / skipped / lỗi).
   - **Generate Report**: chọn DB tổng + date range → generate Excel → mở file.
2. Mỗi operation chạy trong background thread với progress bar.
3. Hiển thị log output trong scrollable text box trong dialog.
4. Chỉ user có permission `admin` mới thấy menu "HQ Tools".

**Acceptance Criteria:**
- [ ] Menu "HQ Tools" chỉ hiện với user role `admin`.
- [ ] Export bundle → file JSON được tạo đúng path.
- [ ] Import bundle → dialog hiển thị "3 imported, 1 skipped (duplicate)".
- [ ] Generate report → file Excel được mở tự động bằng Excel.
- [ ] UI không bị freeze trong khi operation chạy.

---

### TASK-BIZ-04 · Màn hình quản lý User/Audit nâng cao
**Độ phức tạp:** M | **Ưu tiên:** MEDIUM

**Bối cảnh:** Từ `ROADMAP.md` Giai đoạn 6 ⏭: "Màn hình quản trị người dùng/audit nâng cao (lọc, export log)."

**Files cần sửa:**
- `ui/user_management_dialog.py` — thêm: filter theo role, search theo username, export users CSV
- `ui/audit_log_dialog.py` — tạo mới (nếu chưa có): filter theo user/action/date range, export CSV

**Chi tiết thực hiện:**
1. `user_management_dialog.py`:
   - Thêm filter: dropdown chọn role (admin/operator/viewer/all).
   - Search box: lọc theo username (realtime filter, không cần Enter).
   - Cột thêm: "Đăng nhập cuối", "Trạng thái" (active/locked).
   - Nút "Export CSV" xuất danh sách user hiện tại.
2. `audit_log_dialog.py` (tab mới hoặc dialog riêng):
   - Treeview hiển thị audit logs với cột: timestamp, user, action, entity, details.
   - Filter: date range, user, action type.
   - Phân trang (100 records/page).
   - Nút "Export CSV" xuất logs đang lọc.
   - Nút "Dọn dẹp log cũ" gọi `archive_old_logs()` từ TASK-CQ-03.

**Acceptance Criteria:**
- [ ] Filter role → chỉ hiển thị users đúng role.
- [ ] Search username → realtime filter không cần Enter.
- [ ] Export users CSV → file CSV hợp lệ có thể mở Excel.
- [ ] Audit log: filter theo date range → chỉ hiển thị records trong range.
- [ ] Audit log: export CSV → file CSV hợp lệ.

---

## PHASE 6 — DEPLOYMENT VÀ DISTRIBUTION

### TASK-DEPLOY-01 · Auto-Update Mechanism
**Độ phức tạp:** L | **Ưu tiên:** HIGH

**Bối cảnh:** Từ `ROADMAP.md` 7.6: "Auto-update mechanism — Kiểm tra version mới và tự cập nhật. Hiện tại phải cập nhật thủ công."

**Files cần tạo/sửa:**
- `core/update_checker.py` — tạo mới
- `config.py` — thêm `UPDATE_CHECK_URL`, `APP_VERSION`
- `main.py` / `app_controller.py` — gọi update checker khi khởi động

**Chi tiết thực hiện:**
1. `update_checker.py`:
   - Fetch JSON từ `UPDATE_CHECK_URL` (ví dụ: GitHub Releases API).
   - So sánh `latest_version` với `APP_VERSION` dùng `packaging.version`.
   - Trả về `UpdateInfo(available: bool, version: str, download_url: str, changelog: str)`.
2. Chạy check trong background thread khi app khởi động.
3. Nếu có version mới: hiển thị notification banner ở status bar "Có bản cập nhật v1.2.0 — [Xem chi tiết]".
4. Click "Xem chi tiết" → dialog hiển thị changelog + nút "Tải về" (mở browser).
5. Config: `AUTO_CHECK_UPDATE: bool = True` trong `config.py`.

**Acceptance Criteria:**
- [ ] Update check chạy trong background, không block UI.
- [ ] Có version mới → notification banner hiển thị trong 3s sau startup.
- [ ] Click "Tải về" → mở browser đúng URL download.
- [ ] `AUTO_CHECK_UPDATE = False` → không check.
- [ ] Network không có → fail silently (không crash, không error message).

---

### TASK-DEPLOY-02 · Cải thiện Build Pipeline
**Độ phức tạp:** M | **Ưu tiên:** MEDIUM

**Bối cảnh:** `build_exe.ps1` hiện build thủ công, không tích hợp version bumping hoặc changelog.

**Files cần sửa/tạo:**
- `build_exe.ps1` — thêm version injection, checksumming
- `scripts/release.ps1` — tạo mới: full release pipeline
- `.github/workflows/release.yml` — tạo mới: auto-build khi tag release

**Chi tiết thực hiện:**
1. `build_exe.ps1`:
   - Đọc version từ `config.py::APP_VERSION`.
   - Tên output file: `VehicleManagement_v{version}_win64.exe`.
   - Sau khi build: tạo file `SHA256SUMS.txt` chứa hash của .exe.
2. `scripts/release.ps1`:
   - Bump version trong `config.py`.
   - Chạy `pytest` — fail nếu test fail.
   - Chạy `build_exe.ps1`.
   - Tạo git tag `v{version}`.
3. `.github/workflows/release.yml`:
   - Trigger khi push tag `v*.*.*`.
   - Build .exe trên `windows-latest`.
   - Upload .exe và SHA256SUMS.txt vào GitHub Release.

**Acceptance Criteria:**
- [ ] `.\scripts\release.ps1 -Version 1.1.0` → bump version, run tests, build .exe, tạo tag.
- [ ] .exe output có tên đúng format với version.
- [ ] `SHA256SUMS.txt` được tạo cùng thư mục với .exe.
- [ ] Push tag → GitHub Actions tự build và tạo Release.

---

## TỔNG HỢP VÀ THỨ TỰ THI CÔNG

```
Sprint 1 (tuần 1-2) — SECURITY CRITICAL:
  TASK-SEC-01  · Admin password rotation bắt buộc         [M]
  TASK-SEC-02  · Flask dashboard authentication            [M]
  TASK-SEC-03  · SQLite foreign keys ON                   [S]
  TASK-SEC-04  · Transactional Excel import               [M]

Sprint 2 (tuần 3-4) — PERFORMANCE:
  TASK-PERF-01 · Pagination cho stock tab                 [M]
  TASK-PERF-02 · Background owner normalization           [L]
  TASK-CQ-02   · Fix requirements.txt dependencies        [S]

Sprint 3 (tuần 5-6) — CODE QUALITY:
  TASK-CQ-01   · Type hints managers/repos               [L]
  TASK-CQ-03   · Audit log purging                        [M]
  TASK-CQ-04   · Schema versioning & migrations           [M]
  TASK-TEST-02 · GitHub Actions CI pipeline               [M]

Sprint 4 (tuần 7-9) — TESTING + REFACTOR:
  TASK-TEST-01 · Test coverage ≥ 70%                      [XL]
  TASK-PERF-03 · Gộp dashboard (Flask only)              [L]
  TASK-CQ-05   · Refactor main.py                         [XL]

Sprint 5 (tuần 10-12) — BUSINESS FEATURES:
  TASK-BIZ-01  · TRANSFER liên bãi chuẩn hóa             [XL]
  TASK-BIZ-02  · HQ Automation folder watcher             [L]
  TASK-BIZ-03  · HQ tools trong UI                        [L]
  TASK-BIZ-04  · User/Audit management nâng cao           [M]

Sprint 6 (tuần 13-14) — DEPLOYMENT:
  TASK-DEPLOY-01 · Auto-update mechanism                  [L]
  TASK-DEPLOY-02 · Build pipeline cải thiện               [M]
```

---

## ĐỊNH NGHĨA "DONE" (Definition of Done)

Một task được coi là **hoàn thành** khi:
1. Tất cả Acceptance Criteria được đáp ứng.
2. `python -m pytest` pass toàn bộ (không có test nào fail mới).
3. `ruff check .` và `ruff format --check .` pass (zero violations).
4. Không có `print()` statement trong production code (dùng `logging`).
5. Không có `bare except:` (dùng `except SpecificException:`).
6. Code review bởi EA hoặc lead developer.

---

*Roadmap tạo bởi Enterprise Architect — Claude Sonnet 4.6 — 2026-05-22*  
*Dựa trên: CODE_QUALITY_ASSESSMENT.md + ROADMAP.md (existing)*
