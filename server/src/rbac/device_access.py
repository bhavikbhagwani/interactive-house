"""
Device-type access rules (Iteration 4/5).

``caregiver`` is restricted to led, fan, sensor-like, and alarm categories;
door and servo/window devices are denied. Other roles use permission bits only.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from .role_manager import get_user_role
from .roles import (
    Permission,
    ROLE_ADMIN,
    ROLE_CAREGIVER,
    normalize_role,
    role_has_permission,
)

# None = unrestricted by category for this role.
_ROLE_DEVICE_ALLOWLIST: Dict[str, Optional[Set[str]]] = {
    ROLE_ADMIN: None,
    ROLE_CAREGIVER: {
        "led", "fan", "sensor", "light", "lamp", "smoke", "temp",
        "temperature", "humidity", "motion", "alarm",
    },
}


def infer_device_category(device_id: str, device_type: Optional[str] = None) -> str:
    """Map a device to a coarse category for policy checks."""
    if device_type:
        dt = str(device_type).strip().lower()
        if not dt:
            pass
        elif dt in ("led", "light", "lamp"):
            return "led"
        elif dt in ("fan",):
            return "fan"
        elif dt in ("door",):
            return "door"
        elif dt in ("servo", "window", "blinds"):
            return "servo"
        elif dt in ("alarm",):
            return "alarm"
        elif "sensor" in dt or dt in (
            "motion", "smoke", "temperature", "temp", "humidity",
        ):
            return "sensor"
        return dt

    d = (device_id or "").lower()
    if d.startswith(("led-", "light-")) or d.startswith("led"):
        return "led"
    if "door" in d:
        return "door"
    if "fan" in d:
        return "fan"
    if "servo" in d:
        return "servo"
    if any(d.startswith(p) for p in ("motion", "smoke", "temp-", "alarm")):
        return "sensor" if not d.startswith("alarm") else "alarm"
    return "unknown"


def _allowed_categories_for_role(role: str) -> Optional[Set[str]]:
    r = normalize_role(role)
    if r == ROLE_ADMIN:
        return None
    return _ROLE_DEVICE_ALLOWLIST.get(r)


def user_can_access_device(
    user_id: Optional[str],
    device_id: str,
    device_type: Optional[str] = None,
    *,
    need_control: bool = False,
) -> bool:
    if user_id is None:
        return False
    role = get_user_role(str(user_id))
    if role is None:
        return False
    role = normalize_role(role)

    if need_control:
        if not role_has_permission(role, Permission.DEVICE_CONTROL):
            return False
    else:
        if not role_has_permission(role, Permission.DEVICE_VIEW):
            return False

    allow = _allowed_categories_for_role(role)
    if allow is None:
        return True
    cat = infer_device_category(device_id, device_type)
    if role == ROLE_CAREGIVER and cat in ("door", "servo"):
        return False
    return cat in allow


def filter_devices_for_user(
    user_id: Optional[str], devices: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    if user_id is None:
        return []
    out: List[Dict[str, Any]] = []
    for row in devices:
        did = row.get("deviceId", "")
        dt = row.get("deviceType")
        if user_can_access_device(
            str(user_id), str(did), device_type=dt, need_control=False
        ):
            out.append(row)
    return out
