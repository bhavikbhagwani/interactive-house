"""
Role-Based Access Control (RBAC) package.

Introduced in Iteration 4 to restrict what each user can do in the smart
home system depending on their role (admin / family_member / guest).

Public API:
    from src.rbac import (
        Permission,
        ROLES,
        DEFAULT_ROLE,
        role_has_permission,
        get_permissions,
        check_access,
        require_permission,
        enforce_permission,
        AccessDeniedError,
        assign_role,
        revoke_role,
        get_user_role,
        list_users_with_roles,
    )
"""

from .roles import (
    Permission,
    ROLES,
    DEFAULT_ROLE,
    ROLE_ADMIN,
    ROLE_CAREGIVER,
    ROLE_FAMILY_MEMBER,
    ROLE_GUEST,
    role_has_permission,
    get_permissions,
    normalize_role,
)
from .device_access import (
    filter_devices_for_user,
    infer_device_category,
    user_can_access_device,
)
from .access_control import (
    AccessDeniedError,
    check_access,
    require_permission,
    enforce_permission,
)
from .role_manager import (
    assign_role,
    revoke_role,
    get_user_role,
    list_users_with_roles,
)

__all__ = [
    "Permission",
    "ROLES",
    "DEFAULT_ROLE",
    "ROLE_ADMIN",
    "ROLE_CAREGIVER",
    "ROLE_FAMILY_MEMBER",
    "ROLE_GUEST",
    "role_has_permission",
    "get_permissions",
    "normalize_role",
    "AccessDeniedError",
    "check_access",
    "require_permission",
    "enforce_permission",
    "assign_role",
    "revoke_role",
    "get_user_role",
    "list_users_with_roles",
    "filter_devices_for_user",
    "infer_device_category",
    "user_can_access_device",
]
