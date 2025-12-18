"""Database managers package.

This file exists to make the `database` directory a regular Python package.
"""

from .base_manager import BaseManager
from .vehicle_manager import VehicleManager
from .entity_manager import EntityManager
from .dispatch_manager import DispatchManager
from .location_manager import LocationManager
from .audit_repository import (
    AuditRepository,
    AuditEntry,
    AuditAction,
    AuditFilter,
    get_audit_repository,
    log_audit,
    log_create,
    log_update,
    log_delete,
    log_backup,
    log_restore,
)

__all__ = [
    "BaseManager",
    "VehicleManager",
    "EntityManager",
    "DispatchManager",
    "LocationManager",
    # Audit
    "AuditRepository",
    "AuditEntry",
    "AuditAction",
    "AuditFilter",
    "get_audit_repository",
    "log_audit",
    "log_create",
    "log_update",
    "log_delete",
    "log_backup",
    "log_restore",
]
