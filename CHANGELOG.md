# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [5.1.0-alpha] - 2024-12-19

### Phase 1A: Backup/Restore + Audit Logging

#### Added

- **Phase 1A.1**: Database Backup System
  - `core/backup_service.py`: BackupService class with full backup/restore functionality
  - BackupMetadata dataclass for storing backup information
  - Manual and automatic backup types with separate directories
  - SHA-256 checksum verification for backup integrity
  - Backup metadata stored in _backup_meta.json
  - 19 unit tests for backup service

- **Phase 1A.2**: Restore & Verification
  - `restore_backup()`: Restore database from backup with verification
  - `verify_backup()`: Verify backup integrity with checksum and SQLite validation
  - Pre-restore backup creation for rollback safety
  - `get_backup_info()`: Get detailed backup metadata

- **Phase 1A.3**: Audit Logging System
  - `database/audit_repository.py`: AuditRepository with comprehensive logging
  - AuditEntry dataclass and AuditAction enum
  - Track all CRUD operations with old/new values
  - Special actions: BACKUP, RESTORE, LOGIN, LOGOUT, CONFIG_CHANGE, etc.
  - Query/filter/export capabilities
  - Convenience functions: log_create, log_update, log_delete, log_backup, log_restore
  - 30 unit tests for audit repository

- **Phase 1A.4**: Backup/Restore UI
  - `ui/backup_dialog.py`: Full-featured backup management dialog
  - Create manual backups with one-click
  - List and browse existing backups
  - Restore from backup with confirmation
  - Verify backup integrity visually
  - Delete old backups
  - View backup statistics

- **Phase 1A Integration Tests**
  - 13 integration tests for backup + audit interaction
  - Test data preservation through backup/restore cycle
  - Test audit logs included in backups

#### Test Coverage

- **Total tests**: 97 (84 unit + 13 integration)
- All tests passing

---

## [5.0.1] - 2024-12-19

### Phase 0: Stabilization & Test Baseline

#### Added

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

- **Phase 0.2**: Error handling
  - Custom exception hierarchy in exceptions.py
  - VehicleManagementError as base class
  - DatabaseError, ValidationError, SecurityError subtrees
  - SQLInjectionError, InvalidTableNameError for security
  - VINValidationError, DateValidationError, RequiredFieldError for validation

- **Phase 0.3**: Data integrity checks
  - VIN validation before database write (6-17 chars, no I/O/Q)
  - Owner field validation (non-empty required)
  - Date format validation (DD/MM/YYYY or YYYY-MM-DD)
  - Integration with VehicleManager.add_vehicle()

- **Phase 0.4**: Test baseline
  - 35 tests passing, 0 skipped, 0 failed
  - 37% code coverage for database layer
  - 82% coverage for data_normalizer module

#### Changed

- BaseManager now accepts optional `db_path` parameter for testing
- BaseManager._validate_identifier() uses custom exceptions
- Enhanced `setup_logging()` with better documentation

#### Fixed

- Test API compatibility with datetime objects for `add_vehicle()`
- Correct method names in tests (get_all_free_locations vs get_available_locations)
- Location occupy/release test now works independently

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
