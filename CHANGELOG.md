# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Phase 0.0**: Test infrastructure
  - pytest + pytest-cov configuration (pytest.ini)
  - Test fixtures for database isolation (conftest.py)
  - Smoke tests for application imports and config
  - Unit tests for VIN validation, owner normalization
  - Database layer tests for BaseManager, VehicleManager, LocationManager
  - Module-level wrapper functions in data_normalizer.py

- **Phase 0.1**: Logging standardization
  - Module-level loggers in all database managers
  - Standardized log format with module name
  - `get_logger()` utility function for consistent logger creation

### Changed

- BaseManager now accepts optional `db_path` parameter for testing
- Enhanced `setup_logging()` with better documentation

### Fixed

- Test API compatibility with datetime objects for `add_vehicle()`
- Correct method names in tests (get_all_free_locations vs get_available_locations)

---

## [5.0.0] - 2024-12-17

### Initial Release - Baseline V5.0

#### Features

- **Nhập bãi (Inbound)**: Nhập xe mới vào hệ thống với QR scan
- **Xuất bãi lẻ (Outbound)**: Xuất từng xe riêng lẻ
- **Xuất bãi nhiều (Dispatch)**: Tạo phiếu xuất cho nhiều xe
- **Tồn bãi (Stock)**: Xem danh sách xe đang trong bãi
- **Tra cứu (Search)**: Tìm kiếm xe theo nhiều tiêu chí
- **Báo cáo (Dashboard)**: Thống kê và biểu đồ
- **Nhật ký (Log)**: Xem lịch sử hoạt động
- **Lưu trữ (Archive)**: Lưu trữ và tra cứu dữ liệu cũ

#### Technical Stack

- Python 3.x + CustomTkinter
- SQLite Database
- Multi-language support (VI/EN)
- Report generation (Excel, PDF, Word)
- QR Code scanning

#### Known Issues (to be fixed in Phase 0)

- Logging format không chuẩn hóa
- Một số error handling chưa đầy đủ
- Chưa có test automation

---

## Version History

| Version | Date       | Description                    |
|---------|------------|--------------------------------|
| 5.0.0   | 2024-12-17 | Initial baseline release       |
