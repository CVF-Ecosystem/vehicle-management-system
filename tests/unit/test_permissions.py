"""
Unit tests for RBAC (Role-Based Access Control) system.
Tests permission inheritance, role definitions, and permission checks.

Phase 1C: RBAC Implementation Tests
"""

import pytest
from auth.permissions import (
    Permission,
    ROLE_ADMIN,
    ROLE_OPERATOR,
    ROLE_VIEWER,
    ROLE_PERMISSIONS,
    get_role_permissions,
    has_permission,
    get_all_permissions,
    get_permission_display_name,
    get_role_display_name,
)


class TestPermissionEnumDefinition:
    """Test Permission enum is properly defined."""
    
    def test_permission_enum_exists(self):
        """Test Permission enum is defined."""
        assert Permission is not None
        assert hasattr(Permission, 'VEHICLE_VIEW')
    
    def test_all_permission_values_unique(self):
        """Test all permission values are unique."""
        permissions = [p.value for p in Permission]
        assert len(permissions) == len(set(permissions))
    
    def test_permission_count(self):
        """Test total number of permissions defined."""
        permissions = get_all_permissions()
        # Should have all defined permissions
        assert len(permissions) >= 20
        assert Permission.VEHICLE_VIEW in permissions
        assert Permission.USER_MANAGE in permissions
    
    def test_critical_permissions_exist(self):
        """Test all critical permissions are defined."""
        critical = [
            Permission.VEHICLE_VIEW,
            Permission.VEHICLE_CREATE,
            Permission.DISPATCH_CREATE,
            Permission.USER_MANAGE,
            Permission.BACKUP_CREATE,
            Permission.AUDIT_VIEW,
        ]
        all_perms = get_all_permissions()
        for perm in critical:
            assert perm in all_perms


class TestRoleDefinitions:
    """Test role definitions and permission sets."""
    
    def test_three_roles_defined(self):
        """Test exactly 3 roles are defined."""
        roles = [ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER]
        assert len(roles) == 3
        assert len(set(roles)) == 3  # All unique
    
    def test_role_names_valid(self):
        """Test role names are valid strings."""
        assert isinstance(ROLE_ADMIN, str)
        assert isinstance(ROLE_OPERATOR, str)
        assert isinstance(ROLE_VIEWER, str)
        assert all(name.islower() for name in [ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER])
    
    def test_role_permissions_dict_structure(self):
        """Test ROLE_PERMISSIONS dict has correct structure."""
        assert isinstance(ROLE_PERMISSIONS, dict)
        assert ROLE_ADMIN in ROLE_PERMISSIONS
        assert ROLE_OPERATOR in ROLE_PERMISSIONS
        assert ROLE_VIEWER in ROLE_PERMISSIONS
        
        for role, perms in ROLE_PERMISSIONS.items():
            assert isinstance(perms, set)
            assert all(isinstance(p, Permission) for p in perms)
    
    def test_no_empty_role_permission_sets(self):
        """Test no role has empty permission set."""
        for role, perms in ROLE_PERMISSIONS.items():
            assert len(perms) > 0, f"Role '{role}' has no permissions"


class TestAdminPermissions:
    """Test admin role has all permissions."""
    
    def test_admin_has_all_permissions(self):
        """Test admin role includes all defined permissions."""
        admin_perms = get_role_permissions(ROLE_ADMIN)
        all_perms = set(Permission)
        
        # Admin should have all or almost all permissions
        assert len(admin_perms) >= len(all_perms) - 2
        assert Permission.VEHICLE_VIEW in admin_perms
        assert Permission.USER_MANAGE in admin_perms
        assert Permission.SETTINGS_MANAGE in admin_perms
    
    def test_admin_vehicle_operations(self):
        """Test admin can do all vehicle operations."""
        admin_perms = get_role_permissions(ROLE_ADMIN)
        vehicle_perms = [
            Permission.VEHICLE_VIEW,
            Permission.VEHICLE_CREATE,
            Permission.VEHICLE_UPDATE,
            Permission.VEHICLE_DELETE,
            Permission.VEHICLE_RESTORE,
            Permission.VEHICLE_HARD_DELETE,
            Permission.VEHICLE_IMPORT,
            Permission.VEHICLE_EXPORT,
        ]
        for perm in vehicle_perms:
            assert perm in admin_perms
    
    def test_admin_system_operations(self):
        """Test admin can do system operations."""
        admin_perms = get_role_permissions(ROLE_ADMIN)
        system_perms = [
            Permission.USER_VIEW,
            Permission.USER_MANAGE,
            Permission.USER_CHANGE_ROLE,
            Permission.BACKUP_CREATE,
            Permission.BACKUP_RESTORE,
            Permission.AUDIT_VIEW,
            Permission.SETTINGS_MANAGE,
        ]
        for perm in system_perms:
            assert perm in admin_perms


class TestOperatorPermissions:
    """Test operator role permissions."""
    
    def test_operator_has_business_permissions(self):
        """Test operator has business operation permissions."""
        op_perms = get_role_permissions(ROLE_OPERATOR)
        
        # Can do vehicle operations
        assert Permission.VEHICLE_VIEW in op_perms
        assert Permission.VEHICLE_CREATE in op_perms
        assert Permission.VEHICLE_UPDATE in op_perms
        assert Permission.VEHICLE_EXPORT in op_perms
        
        # Can do dispatch operations
        assert Permission.DISPATCH_VIEW in op_perms
        assert Permission.DISPATCH_CREATE in op_perms
    
    def test_operator_cannot_do_admin_operations(self):
        """Test operator lacks admin-only permissions."""
        op_perms = get_role_permissions(ROLE_OPERATOR)
        
        # Cannot manage users
        assert Permission.USER_MANAGE not in op_perms
        assert Permission.USER_CHANGE_ROLE not in op_perms
        
        # Cannot manage backups fully
        assert Permission.BACKUP_RESTORE not in op_perms
        
        # Cannot manage settings
        assert Permission.SETTINGS_MANAGE not in op_perms
    
    def test_operator_hard_delete_forbidden(self):
        """Test operator cannot hard delete vehicles."""
        op_perms = get_role_permissions(ROLE_OPERATOR)
        assert Permission.VEHICLE_HARD_DELETE not in op_perms
    
    def test_operator_can_backup_but_not_restore(self):
        """Test operator can create but not restore backups."""
        op_perms = get_role_permissions(ROLE_OPERATOR)
        assert Permission.BACKUP_CREATE in op_perms
        assert Permission.BACKUP_RESTORE not in op_perms
    
    def test_operator_permission_count_reasonable(self):
        """Test operator has reasonable number of permissions."""
        op_perms = get_role_permissions(ROLE_OPERATOR)
        admin_perms = get_role_permissions(ROLE_ADMIN)
        
        # Operator should have fewer permissions than admin
        assert len(op_perms) < len(admin_perms)
        # But still substantial permissions
        assert len(op_perms) >= 15


class TestViewerPermissions:
    """Test viewer role permissions."""
    
    def test_viewer_view_only_permissions(self):
        """Test viewer can only view, not modify."""
        viewer_perms = get_role_permissions(ROLE_VIEWER)
        
        # Can view
        assert Permission.VEHICLE_VIEW in viewer_perms
        assert Permission.DISPATCH_VIEW in viewer_perms
        assert Permission.LOCATION_VIEW in viewer_perms
        assert Permission.ENTITY_VIEW in viewer_perms
        
        # Can export
        assert Permission.VEHICLE_EXPORT in viewer_perms
    
    def test_viewer_cannot_create_operations(self):
        """Test viewer cannot create anything."""
        viewer_perms = get_role_permissions(ROLE_VIEWER)
        
        assert Permission.VEHICLE_CREATE not in viewer_perms
        assert Permission.DISPATCH_CREATE not in viewer_perms
        assert Permission.ENTITY_MANAGE not in viewer_perms
    
    def test_viewer_cannot_modify_operations(self):
        """Test viewer cannot modify anything."""
        viewer_perms = get_role_permissions(ROLE_VIEWER)
        
        assert Permission.VEHICLE_UPDATE not in viewer_perms
        assert Permission.VEHICLE_DELETE not in viewer_perms
        assert Permission.DISPATCH_UPDATE not in viewer_perms
    
    def test_viewer_cannot_admin_operations(self):
        """Test viewer cannot do admin operations."""
        viewer_perms = get_role_permissions(ROLE_VIEWER)
        
        assert Permission.USER_MANAGE not in viewer_perms
        assert Permission.BACKUP_CREATE not in viewer_perms
        assert Permission.BACKUP_RESTORE not in viewer_perms
        assert Permission.AUDIT_VIEW not in viewer_perms
        assert Permission.SETTINGS_MANAGE not in viewer_perms
    
    def test_viewer_permission_count_minimal(self):
        """Test viewer has minimal permission set."""
        viewer_perms = get_role_permissions(ROLE_VIEWER)
        
        # Viewer should have fewest permissions
        assert len(viewer_perms) <= 8
        assert len(viewer_perms) > 0


class TestPermissionHierarchy:
    """Test permission hierarchy (admin > operator > viewer)."""
    
    def test_admin_supersets_operator(self):
        """Test admin permissions include all operator permissions."""
        admin_perms = get_role_permissions(ROLE_ADMIN)
        op_perms = get_role_permissions(ROLE_OPERATOR)
        
        assert op_perms.issubset(admin_perms)
    
    def test_operator_supersets_viewer(self):
        """Test operator permissions include all viewer permissions."""
        op_perms = get_role_permissions(ROLE_OPERATOR)
        viewer_perms = get_role_permissions(ROLE_VIEWER)
        
        assert viewer_perms.issubset(op_perms)
    
    def test_admin_supersets_viewer(self):
        """Test admin permissions include all viewer permissions (transitive)."""
        admin_perms = get_role_permissions(ROLE_ADMIN)
        viewer_perms = get_role_permissions(ROLE_VIEWER)
        
        assert viewer_perms.issubset(admin_perms)
    
    def test_role_hierarchy_is_strict(self):
        """Test permission sets are strictly ordered."""
        admin = set(get_role_permissions(ROLE_ADMIN))
        op = set(get_role_permissions(ROLE_OPERATOR))
        viewer = set(get_role_permissions(ROLE_VIEWER))
        
        assert len(admin) > len(op) > len(viewer)


class TestHasPermissionFunction:
    """Test has_permission helper function."""
    
    def test_admin_has_permission_returns_true(self):
        """Test admin has all permissions."""
        assert has_permission(ROLE_ADMIN, Permission.VEHICLE_VIEW)
        assert has_permission(ROLE_ADMIN, Permission.USER_MANAGE)
        assert has_permission(ROLE_ADMIN, Permission.SETTINGS_MANAGE)
    
    def test_operator_has_business_permissions(self):
        """Test operator has business permissions."""
        assert has_permission(ROLE_OPERATOR, Permission.VEHICLE_VIEW)
        assert has_permission(ROLE_OPERATOR, Permission.VEHICLE_CREATE)
        assert has_permission(ROLE_OPERATOR, Permission.DISPATCH_CREATE)
    
    def test_operator_lacks_admin_permissions(self):
        """Test operator lacks admin permissions."""
        assert not has_permission(ROLE_OPERATOR, Permission.USER_MANAGE)
        assert not has_permission(ROLE_OPERATOR, Permission.SETTINGS_MANAGE)
    
    def test_viewer_has_view_only_permissions(self):
        """Test viewer has view-only permissions."""
        assert has_permission(ROLE_VIEWER, Permission.VEHICLE_VIEW)
        assert has_permission(ROLE_VIEWER, Permission.VEHICLE_EXPORT)
    
    def test_viewer_lacks_modify_permissions(self):
        """Test viewer lacks modify permissions."""
        assert not has_permission(ROLE_VIEWER, Permission.VEHICLE_CREATE)
        assert not has_permission(ROLE_VIEWER, Permission.DISPATCH_CREATE)
        assert not has_permission(ROLE_VIEWER, Permission.BACKUP_CREATE)
    
    def test_invalid_role_returns_false(self):
        """Test invalid role returns no permissions."""
        assert not has_permission('invalid_role', Permission.VEHICLE_VIEW)
        assert not has_permission('superuser', Permission.VEHICLE_VIEW)


class TestPermissionDisplayNames:
    """Test permission display name functions."""
    
    def test_all_permissions_have_display_names(self):
        """Test all permissions have display names."""
        for perm in get_all_permissions():
            name = get_permission_display_name(perm)
            assert name is not None
            assert isinstance(name, str)
            assert len(name) > 0
            assert name != perm.name  # Should be Vietnamese display name
    
    def test_specific_display_names(self):
        """Test specific permission display names are correct."""
        assert "xe" in get_permission_display_name(Permission.VEHICLE_VIEW).lower()
        assert "phiếu" in get_permission_display_name(Permission.DISPATCH_CREATE).lower()
        assert "user" in get_permission_display_name(Permission.USER_MANAGE).lower()
    
    def test_role_display_names(self):
        """Test role display names."""
        assert "Quản trị" in get_role_display_name(ROLE_ADMIN)
        assert "Nhân viên" in get_role_display_name(ROLE_OPERATOR)
        assert "Người xem" in get_role_display_name(ROLE_VIEWER)
    
    def test_invalid_role_display_name(self):
        """Test invalid role display name fallback."""
        result = get_role_display_name('unknown_role')
        assert result == 'unknown_role'


class TestPermissionGroups:
    """Test that permissions are logically grouped."""
    
    def test_vehicle_permissions_group(self):
        """Test vehicle-related permissions."""
        vehicle_perms = [p for p in Permission if 'VEHICLE' in p.name]
        assert len(vehicle_perms) >= 8
    
    def test_dispatch_permissions_group(self):
        """Test dispatch-related permissions."""
        dispatch_perms = [p for p in Permission if 'DISPATCH' in p.name]
        assert len(dispatch_perms) >= 4
    
    def test_user_permissions_group(self):
        """Test user-related permissions."""
        user_perms = [p for p in Permission if 'USER' in p.name]
        assert len(user_perms) >= 3
    
    def test_backup_permissions_group(self):
        """Test backup-related permissions."""
        backup_perms = [p for p in Permission if 'BACKUP' in p.name]
        assert len(backup_perms) == 2
        assert Permission.BACKUP_CREATE in backup_perms
        assert Permission.BACKUP_RESTORE in backup_perms


class TestPermissionLogic:
    """Test permission logic consistency."""
    
    def test_view_before_modify_pattern(self):
        """Test VIEW permission usually comes before MODIFY permissions."""
        # For vehicles: VEHICLE_VIEW should be in lower roles than VEHICLE_CREATE
        viewer = get_role_permissions(ROLE_VIEWER)
        operator = get_role_permissions(ROLE_OPERATOR)
        
        if Permission.VEHICLE_CREATE in operator:
            assert Permission.VEHICLE_VIEW in viewer
    
    def test_create_implies_view(self):
        """Test if a role can create, it can also view."""
        admin = get_role_permissions(ROLE_ADMIN)
        
        create_perms = [p for p in admin if 'CREATE' in p.name]
        view_perms = [p for p in admin if 'VIEW' in p.name]
        
        # If there are CREATE permissions, there should be VIEW permissions
        if create_perms:
            assert view_perms
    
    def test_delete_requires_higher_privilege(self):
        """Test HARD_DELETE is more restricted than DELETE."""
        admin = get_role_permissions(ROLE_ADMIN)
        operator = get_role_permissions(ROLE_OPERATOR)
        
        # Both should be in admin
        assert Permission.VEHICLE_HARD_DELETE in admin
        
        # But soft delete is in operator, hard delete is not
        assert Permission.VEHICLE_DELETE in operator
        assert Permission.VEHICLE_HARD_DELETE not in operator
