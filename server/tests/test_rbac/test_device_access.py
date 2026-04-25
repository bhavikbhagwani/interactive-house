"""Unit tests for :mod:`src.rbac.device_access` (device-type allowlists + caregiver).

Run::

    cd server
    python tests/test_rbac/test_device_access.py
"""

from __future__ import annotations

import os
import sys
import traceback

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
sys.path.insert(0, _SERVER_DIR)

try:
    from src.rbac import device_access as da  # type: ignore
    from src.rbac import role_manager as rm  # type: ignore
    from src.rbac import roles  # type: ignore
    from src import rbac  # type: ignore
except Exception:
    da = None
    rm = None
    roles = None
    rbac = None
    _import_trace = traceback.format_exc()
else:
    _import_trace = ""
    if rm is not None:
        rm._db_available = lambda: False  # type: ignore[attr-defined]


def print_result(name, status, details=None):
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def _skip(name):
    if da is None or rbac is None:
        print_result(name, "SKIP", _import_trace.splitlines()[-1] if _import_trace else "import failed")
        return True
    return False


def _reset_memory():
    if rm and hasattr(rm, "reset_memory_cache"):
        try:
            rm.reset_memory_cache()
        except Exception:
            pass


def test_infer_device_category_from_type():
    name = "infer_device_category uses deviceType when present"
    if _skip(name):
        return None
    try:
        assert da.infer_device_category("x-1", "door") == "door"
        assert da.infer_device_category("x-1", "fan") == "fan"
        assert da.infer_device_category("x-1", "motion") == "sensor"
        assert da.infer_device_category("x-1", "led") == "led"
        print_result(name, "PASS", None)
        return True
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_infer_device_category_from_device_id():
    name = "infer_device_category falls back to deviceId prefix"
    if _skip(name):
        return None
    try:
        assert da.infer_device_category("led-2", None) == "led"
        assert da.infer_device_category("door-1", None) == "door"
        assert da.infer_device_category("fan-1", None) == "fan"
        print_result(name, "PASS", None)
        return True
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_caregiver_cannot_access_door():
    name = "caregiver denied door/servo; allowed led"
    if _skip(name):
        return None
    try:
        _reset_memory()
        uid = "user-caregiver-1"
        rm.assign_role(uid, roles.ROLE_CAREGIVER)  # type: ignore[union-attr]
        assert not da.user_can_access_device(uid, "door-1", "door", need_control=True)  # type: ignore[union-attr]
        assert not da.user_can_access_device(uid, "servo-1", "servo", need_control=True)  # type: ignore[union-attr]
        assert da.user_can_access_device(uid, "led-1", "led", need_control=True)  # type: ignore[union-attr]
        assert da.user_can_access_device(uid, "fan-1", "fan", need_control=True)  # type: ignore[union-attr]
        print_result(name, "PASS", None)
        return True
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False
    finally:
        _reset_memory()


def test_admin_unrestricted_by_category():
    name = "admin not restricted by device category"
    if _skip(name):
        return None
    try:
        _reset_memory()
        uid = "user-admin-1"
        rm.assign_role(uid, roles.ROLE_ADMIN)  # type: ignore[union-attr]
        assert da.user_can_access_device(uid, "door-1", "door", need_control=True)  # type: ignore[union-attr]
        print_result(name, "PASS", None)
        return True
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False
    finally:
        _reset_memory()


def test_filter_devices_excludes_door_for_caregiver():
    name = "filter_devices_for_user hides door for caregiver"
    if _skip(name):
        return None
    try:
        _reset_memory()
        uid = "user-caregiver-2"
        rm.assign_role(uid, roles.ROLE_CAREGIVER)  # type: ignore[union-attr]
        rows = [
            {"deviceId": "led-1", "deviceType": "led"},
            {"deviceId": "door-1", "deviceType": "door"},
        ]
        out = da.filter_devices_for_user(uid, rows)  # type: ignore[union-attr]
        ids = {r["deviceId"] for r in out}
        passed = "led-1" in ids and "door-1" not in ids
        print_result(name, "PASS" if passed else "FAIL", {"ids": ids})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False
    finally:
        _reset_memory()


def test_primary_user_normalizes_to_admin():
    name = "normalize_role maps primary_user to admin"
    if _skip(name):
        return None
    try:
        assert roles.normalize_role("primary_user") == roles.ROLE_ADMIN  # type: ignore[union-attr]
        print_result(name, "PASS", None)
        return True
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_rbac_exports_device_access():
    name = "rbac package exports user_can_access_device and filter_devices_for_user"
    if _skip(name):
        return None
    try:
        assert hasattr(rbac, "user_can_access_device")
        assert hasattr(rbac, "filter_devices_for_user")
        assert hasattr(roles, "ROLE_CAREGIVER")
        print_result(name, "PASS", None)
        return True
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def main():
    print("Running device_access (RBAC) tests...\n")
    tests = [
        test_infer_device_category_from_type,
        test_infer_device_category_from_device_id,
        test_caregiver_cannot_access_door,
        test_admin_unrestricted_by_category,
        test_filter_devices_excludes_door_for_caregiver,
        test_primary_user_normalizes_to_admin,
        test_rbac_exports_device_access,
    ]
    passed = 0
    for t in tests:
        try:
            r = t()
            if r is True:
                passed += 1
        except Exception as exc:
            print_result(t.__name__, "FAIL", repr(exc))
    print(f"\nSummary: {passed}/{len(tests)} tests passed.")


if __name__ == "__main__":
    main()
