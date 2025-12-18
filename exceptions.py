# exceptions.py
"""
Custom exceptions for Vehicle Management System.

Cung cấp các exception classes chuẩn hóa cho toàn bộ ứng dụng.
Giúp phân loại lỗi và xử lý một cách nhất quán.
"""


class VehicleManagementError(Exception):
    """Base exception class for all application errors."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        """
        Initialize exception.
        
        Args:
            message: Human-readable error message
            code: Optional error code for programmatic handling
            details: Optional dict with additional context
        """
        super().__init__(message)
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for logging/API responses."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


# =============================================================================
# Database Exceptions
# =============================================================================

class DatabaseError(VehicleManagementError):
    """Base exception for database-related errors."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message, code or "DATABASE_ERROR", details)


class ConnectionError(DatabaseError):
    """Failed to connect to database."""
    
    def __init__(self, db_path: str, original_error: Exception = None):
        details = {"db_path": db_path}
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(
            f"Không thể kết nối đến database: {db_path}",
            "DB_CONNECTION_ERROR",
            details
        )


class SchemaError(DatabaseError):
    """Database schema is invalid or migration failed."""
    
    def __init__(self, message: str, table: str = None):
        details = {}
        if table:
            details["table"] = table
        super().__init__(message, "DB_SCHEMA_ERROR", details)


class IntegrityError(DatabaseError):
    """Data integrity constraint violation (unique, foreign key, etc.)."""
    
    def __init__(self, message: str, constraint: str = None, value: str = None):
        details = {}
        if constraint:
            details["constraint"] = constraint
        if value:
            details["value"] = value
        super().__init__(message, "DB_INTEGRITY_ERROR", details)


class RecordNotFoundError(DatabaseError):
    """Requested record does not exist."""
    
    def __init__(self, entity: str, identifier: str):
        super().__init__(
            f"Không tìm thấy {entity}: {identifier}",
            "RECORD_NOT_FOUND",
            {"entity": entity, "identifier": identifier}
        )


# =============================================================================
# Validation Exceptions
# =============================================================================

class ValidationError(VehicleManagementError):
    """Base exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, code: str = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(message, code or "VALIDATION_ERROR", details)


class VINValidationError(ValidationError):
    """Invalid VIN format or checksum."""
    
    def __init__(self, vin: str, reason: str = None, message: str = None):
        # Cho phép tùy chỉnh message hoặc tự tạo
        if message:
            final_message = message
        else:
            final_message = f"VIN không hợp lệ: {vin}"
            if reason:
                final_message += f" - {reason}"
        super().__init__(final_message, "vin", "INVALID_VIN")
        self.details["vin"] = vin
        if reason:
            self.details["reason"] = reason


class DateValidationError(ValidationError):
    """Invalid date format or value."""
    
    def __init__(self, value: str = None, expected_format: str = None, field_name: str = None, message: str = None):
        if message:
            final_message = message
        else:
            final_message = f"Ngày không hợp lệ: {value}"
            if expected_format:
                final_message += f" (expected: {expected_format})"
        super().__init__(final_message, field_name or "date", "INVALID_DATE")
        if value:
            self.details["value"] = value
        if expected_format:
            self.details["expected_format"] = expected_format


class RequiredFieldError(ValidationError):
    """Required field is missing or empty."""
    
    def __init__(self, field_name: str = None, message: str = None, field: str = None):
        # Support cả field_name và field cho backward compatibility
        actual_field = field_name or field or "unknown"
        final_message = message or f"Trường bắt buộc không được để trống: {actual_field}"
        super().__init__(
            final_message,
            actual_field,
            "REQUIRED_FIELD"
        )


# =============================================================================
# Business Logic Exceptions
# =============================================================================

class BusinessError(VehicleManagementError):
    """Base exception for business logic errors."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message, code or "BUSINESS_ERROR", details)


class DuplicateVINError(BusinessError):
    """VIN already exists in the system."""
    
    def __init__(self, vin: str, status: str = None):
        details = {"vin": vin}
        if status:
            details["current_status"] = status
        super().__init__(
            f"VIN đã tồn tại trong hệ thống: {vin}",
            "DUPLICATE_VIN",
            details
        )


class VehicleNotInStockError(BusinessError):
    """Vehicle is not in stock (already shipped or inactive)."""
    
    def __init__(self, vin: str, current_status: str = None):
        details = {"vin": vin}
        if current_status:
            details["current_status"] = current_status
        super().__init__(
            f"Xe không có trong bãi: {vin}",
            "VEHICLE_NOT_IN_STOCK",
            details
        )


class LocationOccupiedError(BusinessError):
    """Location is already occupied by another vehicle."""
    
    def __init__(self, location_name: str, occupied_by_vin: str = None):
        details = {"location": location_name}
        if occupied_by_vin:
            details["occupied_by"] = occupied_by_vin
        super().__init__(
            f"Vị trí đã bị chiếm: {location_name}",
            "LOCATION_OCCUPIED",
            details
        )


class NoAvailableLocationError(BusinessError):
    """No free locations available in the yard."""
    
    def __init__(self):
        super().__init__(
            "Không còn vị trí trống trong bãi",
            "NO_AVAILABLE_LOCATION"
        )


class DispatchError(BusinessError):
    """Error related to dispatch/shipment operations."""
    
    def __init__(self, message: str, dispatch_id: int = None):
        details = {}
        if dispatch_id:
            details["dispatch_id"] = dispatch_id
        super().__init__(message, "DISPATCH_ERROR", details)


class DispatchNotFoundError(DispatchError):
    """Dispatch record not found."""
    
    def __init__(self, dispatch_id: int):
        super().__init__(
            f"Không tìm thấy phiếu xuất: #{dispatch_id}",
            dispatch_id
        )
        self.code = "DISPATCH_NOT_FOUND"


class DispatchAlreadyCompletedError(DispatchError):
    """Dispatch is already completed, cannot modify."""
    
    def __init__(self, dispatch_id: int):
        super().__init__(
            f"Phiếu xuất #{dispatch_id} đã hoàn tất, không thể sửa đổi",
            dispatch_id
        )
        self.code = "DISPATCH_ALREADY_COMPLETED"


# =============================================================================
# Security Exceptions
# =============================================================================

class SecurityError(VehicleManagementError):
    """Base exception for security-related errors."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message, code or "SECURITY_ERROR", details)


class SQLInjectionError(SecurityError):
    """Potential SQL injection attempt detected."""
    
    def __init__(self, message: str = None, input_value: str = None):
        details = {}
        if input_value is not None:
            details["input_value"] = input_value
        super().__init__(
            message or f"Invalid input detected (possible SQL injection)",
            "SQL_INJECTION_DETECTED",
            details
        )


class InvalidTableNameError(SecurityError):
    """Table name not in whitelist."""
    
    def __init__(self, table_name: str, valid_tables: list = None):
        details = {"table_name": table_name}
        if valid_tables:
            details["valid_tables"] = valid_tables
        super().__init__(
            f"Invalid table name: {table_name}",
            "INVALID_TABLE_NAME",
            details
        )


# =============================================================================
# Import/Export Exceptions
# =============================================================================

class ImportError(VehicleManagementError):
    """Error during data import."""
    
    def __init__(self, message: str, row: int = None, file_path: str = None):
        details = {}
        if row is not None:
            details["row"] = row
        if file_path:
            details["file"] = file_path
        super().__init__(message, "IMPORT_ERROR", details)


class ExportError(VehicleManagementError):
    """Error during data export/report generation."""
    
    def __init__(self, message: str, report_type: str = None):
        details = {}
        if report_type:
            details["report_type"] = report_type
        super().__init__(message, "EXPORT_ERROR", details)
