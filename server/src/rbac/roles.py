"""
Role and permission definitions for the smart home RBAC system.

Three roles are supported in Iteration 4:

- admin          : full access to every feature, including admin settings,
                   role assignment and automation management.
- family_member  : normal household user. Can view and control devices,
                   view/trigger/create/delete scenes, and view sensors and
                   automation rules. Cannot touch admin-only settings or
                   manage user roles. (New category in Iteration 4.)
- guest          : very limited access. View-only for devices and scenes,
                   no control or write access at all.

Legacy users seeded in earlier iterations used the role string "user".
For backward compatibility we treat "user" and human-readable
``family`` / ``family member`` as aliases of ``family_member`` through
:func:`normalize_role`.
"""

from typing import Dict, FrozenSet


class Permission:
    """Permission constants used across all features."""

    # Device permissions
    DEVICE_VIEW = "device:view"
    DEVICE_CONTROL = "device:control"

    # Scene permissions
    SCENE_VIEW = "scene:view"
    SCENE_TRIGGER = "scene:trigger"
    SCENE_CREATE = "scene:create"
    SCENE_DELETE = "scene:delete"

    # Sensor / automation permissions
    SENSOR_VIEW = "sensor:view"
    SENSOR_MANAGE = "sensor:manage"
    AUTOMATION_VIEW = "automation:view"
    AUTOMATION_MANAGE = "automation:manage"

    # Admin-only permissions
    ROLE_ASSIGN = "role:assign"
    USER_MANAGE = "user:manage"
    SETTINGS_ADMIN = "settings:admin"


# Role name constants (avoid typos at call sites).
ROLE_ADMIN = "admin"
ROLE_FAMILY_MEMBER = "family_member"
ROLE_GUEST = "guest"
ROLE_CAREGIVER = "caregiver"

DEFAULT_ROLE = ROLE_FAMILY_MEMBER

_CAREGIVER_PERMS = frozenset({
    Permission.DEVICE_VIEW,
    Permission.DEVICE_CONTROL,
    Permission.SCENE_VIEW,
    Permission.SCENE_TRIGGER,
    Permission.SENSOR_VIEW,
    Permission.AUTOMATION_VIEW,
})


# Role -> permissions mapping. Frozenset so individual role sets are
# immutable once defined at import time.
ROLES: Dict[str, FrozenSet[str]] = {
    ROLE_ADMIN: frozenset({
        Permission.DEVICE_VIEW,
        Permission.DEVICE_CONTROL,
        Permission.SCENE_VIEW,
        Permission.SCENE_TRIGGER,
        Permission.SCENE_CREATE,
        Permission.SCENE_DELETE,
        Permission.SENSOR_VIEW,
        Permission.SENSOR_MANAGE,
        Permission.AUTOMATION_VIEW,
        Permission.AUTOMATION_MANAGE,
        Permission.ROLE_ASSIGN,
        Permission.USER_MANAGE,
        Permission.SETTINGS_ADMIN,
    }),
    ROLE_FAMILY_MEMBER: frozenset({
        Permission.DEVICE_VIEW,
        Permission.DEVICE_CONTROL,
        Permission.SCENE_VIEW,
        Permission.SCENE_TRIGGER,
        Permission.SCENE_CREATE,
        Permission.SCENE_DELETE,
        Permission.SENSOR_VIEW,
        Permission.AUTOMATION_VIEW,
    }),
    ROLE_GUEST: frozenset({
        Permission.DEVICE_VIEW,
        Permission.SCENE_VIEW,
    }),
    ROLE_CAREGIVER: _CAREGIVER_PERMS,
}


# Roles that existed in earlier iterations are mapped into the new model so
# that previously seeded users keep working after upgrade.
_ROLE_ALIASES: Dict[str, str] = {
    "user": ROLE_FAMILY_MEMBER,
    "unit": ROLE_FAMILY_MEMBER,
    "family": ROLE_FAMILY_MEMBER,
    "family member": ROLE_FAMILY_MEMBER,
    "primary_user": ROLE_ADMIN,
}


def normalize_role(role):
    """Return a canonical role name. Unknown or empty roles fall back to the
    default (family_member) so legacy data does not break authentication."""
    if not role:
        return DEFAULT_ROLE
    role = str(role).strip().lower()
    if role in ROLES:
        return role
    return _ROLE_ALIASES.get(role, DEFAULT_ROLE)


def get_permissions(role):
    """Return the frozenset of permissions granted to a role."""
    return ROLES.get(normalize_role(role), frozenset())


def role_has_permission(role, permission):
    """Return True if the given role is allowed to perform ``permission``."""
    if not permission:
        return False
    return permission in get_permissions(role)
