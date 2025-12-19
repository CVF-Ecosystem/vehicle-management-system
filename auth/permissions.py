# auth/permissions.py
"""
Role-Based Access Control (RBAC) - Phase 1C
Định nghĩa các quyền và vai trò trong hệ thống.
"""

from enum import Enum, auto
from typing import Set, Dict

# Role constants
ROLE_ADMIN = 'admin'
ROLE_OPERATOR = 'operator'
ROLE_VIEWER = 'viewer'


class Permission(Enum):
    """Enum định nghĩa các quyền trong hệ thống."""
    
    # Vehicle permissions
    VEHICLE_VIEW = auto()           # Xem danh sách xe
    VEHICLE_CREATE = auto()         # Thêm xe mới (nhập bãi)
    VEHICLE_UPDATE = auto()         # Cập nhật thông tin xe
    VEHICLE_DELETE = auto()         # Xóa xe (soft delete)
    VEHICLE_RESTORE = auto()        # Khôi phục xe đã xóa
    VEHICLE_HARD_DELETE = auto()    # Xóa vĩnh viễn
    VEHICLE_IMPORT = auto()         # Import từ Excel
    VEHICLE_EXPORT = auto()         # Export báo cáo
    
    # Dispatch permissions
    DISPATCH_VIEW = auto()          # Xem phiếu xuất
    DISPATCH_CREATE = auto()        # Tạo phiếu xuất (xuất bãi)
    DISPATCH_UPDATE = auto()        # Cập nhật phiếu
    DISPATCH_DELETE = auto()        # Xóa phiếu
    
    # Location permissions
    LOCATION_VIEW = auto()          # Xem layout bãi
    LOCATION_MANAGE = auto()        # Quản lý vị trí bãi
    
    # Entity permissions (drivers, transport vehicles)
    ENTITY_VIEW = auto()            # Xem danh sách
    ENTITY_MANAGE = auto()          # Thêm/sửa/xóa
    
    # System permissions
    USER_VIEW = auto()              # Xem danh sách user
    USER_MANAGE = auto()            # Quản lý user (CRUD)
    USER_CHANGE_ROLE = auto()       # Đổi role user
    
    BACKUP_CREATE = auto()          # Tạo backup
    BACKUP_RESTORE = auto()         # Restore backup
    
    AUDIT_VIEW = auto()             # Xem audit log
    SETTINGS_VIEW = auto()          # Xem cài đặt
    SETTINGS_MANAGE = auto()        # Thay đổi cài đặt


# Permission sets for each role
ROLE_PERMISSIONS: Dict[str, Set[Permission]] = {
    ROLE_ADMIN: {
        # Admin có tất cả quyền
        Permission.VEHICLE_VIEW,
        Permission.VEHICLE_CREATE,
        Permission.VEHICLE_UPDATE,
        Permission.VEHICLE_DELETE,
        Permission.VEHICLE_RESTORE,
        Permission.VEHICLE_HARD_DELETE,
        Permission.VEHICLE_IMPORT,
        Permission.VEHICLE_EXPORT,
        
        Permission.DISPATCH_VIEW,
        Permission.DISPATCH_CREATE,
        Permission.DISPATCH_UPDATE,
        Permission.DISPATCH_DELETE,
        
        Permission.LOCATION_VIEW,
        Permission.LOCATION_MANAGE,
        
        Permission.ENTITY_VIEW,
        Permission.ENTITY_MANAGE,
        
        Permission.USER_VIEW,
        Permission.USER_MANAGE,
        Permission.USER_CHANGE_ROLE,
        
        Permission.BACKUP_CREATE,
        Permission.BACKUP_RESTORE,
        
        Permission.AUDIT_VIEW,
        Permission.SETTINGS_VIEW,
        Permission.SETTINGS_MANAGE,
    },
    
    ROLE_OPERATOR: {
        # Operator: thao tác nghiệp vụ, không quản lý hệ thống
        Permission.VEHICLE_VIEW,
        Permission.VEHICLE_CREATE,
        Permission.VEHICLE_UPDATE,
        Permission.VEHICLE_DELETE,      # Soft delete only
        Permission.VEHICLE_RESTORE,
        Permission.VEHICLE_IMPORT,
        Permission.VEHICLE_EXPORT,
        
        Permission.DISPATCH_VIEW,
        Permission.DISPATCH_CREATE,
        Permission.DISPATCH_UPDATE,
        
        Permission.LOCATION_VIEW,
        Permission.LOCATION_MANAGE,     # Có thể quản lý vị trí
        
        Permission.ENTITY_VIEW,
        Permission.ENTITY_MANAGE,       # Có thể quản lý tài xế/xe VC
        
        Permission.BACKUP_CREATE,       # Có thể tạo backup
        
        Permission.SETTINGS_VIEW,
    },
    
    ROLE_VIEWER: {
        # Viewer: chỉ xem và xuất báo cáo
        Permission.VEHICLE_VIEW,
        Permission.VEHICLE_EXPORT,
        
        Permission.DISPATCH_VIEW,
        
        Permission.LOCATION_VIEW,
        
        Permission.ENTITY_VIEW,
        
        Permission.SETTINGS_VIEW,
    },
}


def get_role_permissions(role: str) -> Set[Permission]:
    """
    Lấy danh sách quyền của một role.
    
    Args:
        role: Tên role (admin/operator/viewer)
    
    Returns:
        Set[Permission]: Tập hợp các quyền
    """
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: str, permission: Permission) -> bool:
    """
    Kiểm tra role có quyền cụ thể không.
    
    Args:
        role: Tên role
        permission: Quyền cần kiểm tra
    
    Returns:
        bool: True nếu có quyền
    """
    permissions = get_role_permissions(role)
    return permission in permissions


def get_all_permissions() -> list:
    """Lấy danh sách tất cả các quyền."""
    return list(Permission)


def get_permission_display_name(permission: Permission) -> str:
    """Lấy tên hiển thị của quyền."""
    display_names = {
        Permission.VEHICLE_VIEW: "Xem danh sách xe",
        Permission.VEHICLE_CREATE: "Thêm xe (Nhập bãi)",
        Permission.VEHICLE_UPDATE: "Cập nhật thông tin xe",
        Permission.VEHICLE_DELETE: "Xóa xe",
        Permission.VEHICLE_RESTORE: "Khôi phục xe đã xóa",
        Permission.VEHICLE_HARD_DELETE: "Xóa vĩnh viễn",
        Permission.VEHICLE_IMPORT: "Import từ Excel",
        Permission.VEHICLE_EXPORT: "Xuất báo cáo",
        
        Permission.DISPATCH_VIEW: "Xem phiếu xuất",
        Permission.DISPATCH_CREATE: "Tạo phiếu xuất",
        Permission.DISPATCH_UPDATE: "Cập nhật phiếu xuất",
        Permission.DISPATCH_DELETE: "Xóa phiếu xuất",
        
        Permission.LOCATION_VIEW: "Xem layout bãi",
        Permission.LOCATION_MANAGE: "Quản lý vị trí bãi",
        
        Permission.ENTITY_VIEW: "Xem tài xế/xe VC",
        Permission.ENTITY_MANAGE: "Quản lý tài xế/xe VC",
        
        Permission.USER_VIEW: "Xem danh sách user",
        Permission.USER_MANAGE: "Quản lý user",
        Permission.USER_CHANGE_ROLE: "Đổi role user",
        
        Permission.BACKUP_CREATE: "Tạo backup",
        Permission.BACKUP_RESTORE: "Restore backup",
        
        Permission.AUDIT_VIEW: "Xem nhật ký hệ thống",
        Permission.SETTINGS_VIEW: "Xem cài đặt",
        Permission.SETTINGS_MANAGE: "Thay đổi cài đặt",
    }
    return display_names.get(permission, permission.name)


def get_role_display_name(role: str) -> str:
    """Lấy tên hiển thị của role."""
    display_names = {
        ROLE_ADMIN: "Quản trị viên",
        ROLE_OPERATOR: "Nhân viên",
        ROLE_VIEWER: "Chỉ xem",
    }
    return display_names.get(role, role)
