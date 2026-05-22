# Enterprise Architecture — Code Quality Assessment
## Vehicle Management System
**Ngày đánh giá:** 2026-05-22  
**Đánh giá bởi:** Enterprise Architect Review (Claude Sonnet 4.6)  
**Phiên bản ứng dụng:** 1.0.0

---

## 1. ĐIỂM TỔNG HỢP

| Chiều đánh giá | Điểm | Ghi chú |
|----------------|------|---------|
| Thiết kế kiến trúc | **B+** | Layered MVC rõ ràng — bị kéo xuống do UI monolith |
| Bảo mật | **B+** | RBAC, bcrypt, audit log, rate limiting — yếu ở default credentials |
| Toàn vẹn dữ liệu | **B** | SQLite FK bị tắt; import Excel không có transaction |
| Hiệu năng | **C+** | O(n²) khi khởi động; không có phân trang |
| Độ phủ test | **C** | ~27 file test cho 50+ module; không có UI test |
| Tài liệu | **B** | README/ROADMAP tốt; thiếu sơ đồ kiến trúc |
| Khả năng bảo trì | **B** | 2 dashboard trùng lặp; thiếu type hints |
| **Tổng** | **B** | Production-viable với các gap đã được ghi nhận |

---

## 2. SƠ ĐỒ KIẾN TRÚC TỔNG QUAN

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│   CustomTkinter UI (main.py + ui/)          [Desktop App]  │
│   Streamlit Dashboard (web_dashboard.py)  ──┐              │
│   Flask API Dashboard (dashboard_api.py)  ──┘ DUAL DEBT    │
├─────────────────────────────────────────────────────────────┤
│                  BUSINESS LOGIC LAYER                       │
│   auth/auth_manager.py   |  core/backup_service.py         │
│   auth/permissions.py    |  core/notification_service.py   │
├─────────────────────────────────────────────────────────────┤
│                   DATA ACCESS LAYER                         │
│   database/base_manager.py (Singleton + Thread-safe)       │
│   vehicle_manager | dispatch_manager | entity_manager      │
│   user_repository | audit_repository                       │
├─────────────────────────────────────────────────────────────┤
│             DATA VALIDATION / NORMALIZATION                 │
│   data_normalizer.py  |  excel_importer.py                 │
├─────────────────────────────────────────────────────────────┤
│   SQLite: vehicles.db (xe)  |  security.db (user/audit)   │
└─────────────────────────────────────────────────────────────┘
```

**Điểm mạnh kiến trúc:**
- Phân tầng rõ ràng với manager/repository pattern
- 2 database tách biệt theo domain (xe vs bảo mật) — defense-in-depth tốt
- Offline-first, multi-site bundle export — sáng tạo và phù hợp thực tế
- RBAC với 23+ quyền chi tiết qua decorator `@require_permission`

**Điểm yếu kiến trúc:**
- `main.py` 808 dòng, trộn lẫn UI layout / event handling / business logic
- Hai implementation dashboard (Streamlit + Flask) với SQL query trùng lặp
- Không có service layer giữa UI tabs và managers

---

## 3. ĐÁNH GIÁ BẢO MẬT

### Điểm mạnh
| Control | Triển khai |
|---------|-----------|
| Password hashing | bcrypt 4.3.0 ✓ |
| Session timeout | 30 phút idle, kiểm tra trên mọi permission check ✓ |
| Brute-force protection | 5 lần thất bại → khóa 15 phút; rate limit 10 lần/60s ✓ |
| Phân quyền | RBAC 23+ quyền chi tiết + decorator `@require_permission` ✓ |
| Audit trail | Append-only log với user tracking ✓ |
| Backup encryption | AES-256 tùy chọn qua thư viện `cryptography` ✓ |
| SQL injection | Parameterized queries toàn bộ; whitelist table name ✓ |
| Soft delete | Xe xóa được lưu vào `deleted_vehicles_archive` ✓ |

### Lỗ hổng bảo mật (theo độ ưu tiên)
| # | Mức độ | Vấn đề | Vị trí |
|---|--------|--------|--------|
| 1 | **CAO** | Default `admin/admin123` hardcode — không bắt buộc đổi lần đầu | `user_repository.py` |
| 2 | **CAO** | Flask dashboard không có xác thực, không HTTPS, không CSRF token | `dashboard_api.py` |
| 3 | **TRUNG** | SQLite foreign key constraint OFF mặc định — không CASCADE | `base_manager.py` |
| 4 | **TRUNG** | Không ngăn concurrent session — user có thể đăng nhập 2 lần | `auth_manager.py` |
| 5 | **THẤP** | Không kiểm tra độ phức tạp mật khẩu | `user_repository.py` |
| 6 | **THẤP** | Thư viện `cryptography` thiếu trong `requirements.txt` — silent fail | `backup_service.py` |

---

## 4. TẦNG DỮ LIỆU

### Thiết kế Schema
- 8 bảng với soft-delete archive (`deleted_vehicles_archive`) — tốt
- VIN là PRIMARY KEY — gặp vấn đề khi import VIN trùng
- Không có schema version tracking — cần SQL thủ công khi migration
- Audit log không có cơ chế xóa tự động → tăng trưởng vô hạn

### Lỗ hổng toàn vẹn dữ liệu

```
excel_importer.py — LỖ HỔNG NGHIÊM TRỌNG:
  ✗ Không có database transaction bao quanh vòng import
  ✗ Import một phần có thể xảy ra khi lỗi (50/200 rows commit, rồi crash)
  ✗ Phát hiện VIN trùng xảy ra SAU khi parse (thất bại muộn)
  ✗ Lỗi progress callback bị nuốt silently
```

### Hiệu năng
| Vấn đề | Vị trí | Tác động |
|--------|--------|----------|
| O(n²) chuẩn hóa phonetic owner chạy mỗi lần khởi động | `vehicle_manager.py:36-54` | 5–30s delay với dataset lớn |
| Không phân trang — fetch toàn bộ xe | `stock_tab.py` | Bloat bộ nhớ với 1000+ records |
| Không cache query — chạy lại trên mỗi tab switch | Nhiều tab | DB round-trips không cần thiết |
| Kiểm tra notification đồng bộ — chặn UI thread | `notification_service.py` | UI freeze |

---

## 5. VẤN ĐỀ CHẤT LƯỢNG CODE

### Anti-patterns phát hiện

| Pattern | Vị trí | Mức độ |
|---------|--------|--------|
| **God Class** — 808 dòng, nhiều trách nhiệm | `main.py` | Trung bình |
| **Dual Implementation** — Streamlit + Flask cùng chức năng | `web_dashboard.py` / `dashboard_api.py` | Trung bình |
| **Silent Exception Swallowing** | `excel_importer.py:91-94` | Trung bình |
| **Expensive Startup Side Effect** | `vehicle_manager.py` init | Trung bình |
| **Thiếu Type Hints** trên hầu hết các module | Toàn codebase | Trung bình |
| **Hardcoded Port** `8502` | `web_dashboard_manager.py` | Thấp |
| **Thiếu Pagination** trên query danh sách lớn | `stock_tab.py` | Trung bình |
| **Dependency trùng lặp** — cả `thefuzz` và `RapidFuzz` | `requirements.txt` | Thấp |

### Điểm tốt của codebase
- `ruff.toml` cấu hình với rule set hợp lý (E, W, F, I, B, C4, UP, SIM, RUF)
- `conftest.py` bảo vệ production DB qua SHA256 hash — excellent safety guard
- Phase markers trong code (`# === PHASE 3: ===`) hỗ trợ navigation
- Security comments tham chiếu ROADMAP ID (e.g., `7.3-SEC-1`) — traceable decisions
- CQ fixes tháng 2/2026 đã giải quyết 16/16 mục: bare except, dead code, thread safety

---

## 6. ĐÁNH GIÁ TESTING

```
Ước tính coverage: ~40-50% modules
Test files: ~27 cho 50+ modules

✅ Có test:      auth, backup, normalizers, audit, soft-delete, CRUD cơ bản
⚠️ Partial:      integration workflow, edge cases
❌ Chưa test:    UI layer, concurrency, dashboard API, excel importer transactions,
                 notification service, report generators
```

**Fixture design trong `conftest.py` xuất sắc:**
- `protect_production_db` — hash-guard DB sản xuất trong test run
- `force_test_db` — monkeypatch config per-test isolation
- `sample_db` / `edge_case_db` — test data thực tế với tiếng Việt

**Gap quan trọng:** Không có concurrency test cho thread-safe singleton ở `base_manager.py`.

---

## 7. KIỂM TRA DEPENDENCY

```
requirements.txt:
  ✅ Versions pinned (reproducible builds)
  ✅ bcrypt, RapidFuzz, unidecode (lựa chọn phù hợp)
  ⚠️  cryptography KHÔNG có trong list (backup encryption silently degrades)
  ⚠️  pandas nặng cho use case này (sqlite3 + csv đủ dùng)
  ⚠️  thefuzz VÀ RapidFuzz cùng tồn tại (RapidFuzz là drop-in replacement nhanh hơn — xóa thefuzz)
  ⚠️  Không có hash pinning (pip install có thể kéo transitive deps khác nhau)
```

---

## 8. KHUYẾN NGHỊ THEO ƯU TIÊN

### Ngay lập tức (Sprint 1–2)
1. **Bắt buộc đổi mật khẩu admin** lần đăng nhập đầu — block app cho đến khi đổi; xóa default hardcode
2. **Thêm xác thực vào Flask dashboard** — token-based hoặc session cookie; thêm CORS/CSRF
3. **Bật SQLite foreign keys** — thêm `PRAGMA foreign_keys = ON` trong `base_manager.py`
4. **Wrap `excel_importer` trong transaction** — `BEGIN`/`ROLLBACK` khi có lỗi; kiểm tra VIN trùng trước

### Ngắn hạn (Sprint 3–6)
5. **Thêm phân trang** cho `stock_tab` — 100 records/lần với "Load more"
6. **Chuyển owner normalization sang background thread** — chạy off main thread; cache ra JSON
7. **Gộp hai dashboard** — chọn Flask hoặc Streamlit; xóa cái còn lại
8. **Thêm `cryptography` vào `requirements.txt`** — hoặc warning khi thiếu mà encryption = ON

### Trung hạn (Sprint 7–12)
9. **Refactor `main.py`** — tách mỗi tab thành controller class riêng; `main.py` chỉ còn bootstrap
10. **Thêm type hints + mypy** — ưu tiên manager và repository classes
11. **Implement audit log purging** — tự xóa log >365 ngày vào secondary table
12. **Schema versioning** — bảng `_meta` lưu `schema_version`; migration script per version
13. **Xóa `thefuzz`** — RapidFuzz là drop-in replacement nhanh hơn

### Dài hạn (Phase 5–7 trong ROADMAP)
14. **GitHub Actions CI/CD** — pytest chạy tự động khi push/PR
15. **Test coverage ≥ 80%** — ưu tiên excel importer, notification service, dashboard API
16. **HQ automation** — import theo thư mục, Task Scheduler
17. **Tích hợp công cụ HQ vào UI** — không cần CLI để export/import bundle

---

## 9. KẾT LUẬN

**Codebase có kiến trúc vững chắc cho ứng dụng desktop line-of-business.** Xác thực, phân quyền và audit trail đạt chuẩn production. Thiết kế offline-first multi-site bundle thể hiện tư duy kiến trúc phù hợp với thực tế triển khai (bãi xe thiếu kết nối mạng ổn định).

**Rủi ro chính:**
- **Bảo mật defaults** (mật khẩu admin, dashboard không bảo vệ)
- **Toàn vẹn dữ liệu** (import không transactional, FK bị tắt)
- **Ngưỡng hiệu năng** (không phân trang, tác vụ nặng ở startup)

Không có mục nào yêu cầu rewrite kiến trúc — tất cả là các fix có mục tiêu trên nền tảng đã vững. Giải quyết mục 1–4 trong sprint tiếp theo sẽ nâng security posture từ **B+** lên **A-**.

---

*Đánh giá bởi Enterprise Architect — Claude Sonnet 4.6 — 2026-05-22*
