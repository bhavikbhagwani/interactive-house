"""Extended RBAC and device access tests (roles, permissions, enforcement).

Run from ``server/``::

    python tests/test_rbac/test_rbac_extended.py
"""

from __future__ import annotations

import os
import sys
import traceback

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
sys.path.insert(0, _SERVER_DIR)

try:
    from src import rbac  # type: ignore
    from src.rbac import (  # noqa: E402
        device_access as da,
        role_manager as rm,
    )
    from src.rbac import roles  # type: ignore
except Exception:
    rbac = None
    da = None
    rm = None
    roles = None
    _trace = traceback.format_exc()
else:
    _trace = ""
    if rm is not None:
        rm._db_available = lambda: False  # type: ignore[attr-defined]


def print_result(name: str, status: str, details=None) -> None:
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def _reset():
    if rm and hasattr(rm, "reset_memory_cache"):
        try:
            rm.reset_memory_cache()
        except Exception:
            pass


def test_caregiver_in_roles_table():
    name = "ROLE_CAREGIVER is defined and has a permission set"
    if rbac is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        r = roles.ROLE_CAREGIVER  # type: ignore[union-attr]
        p = rbac.ROLES.get(r)  # type: ignore[union-attr]
        passed = p is not None and rbac.Permission.DEVICE_CONTROL in p
        print_result(name, "PASS" if passed else "FAIL", {r: list(p) if p else None})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_primary_user_resolves_in_assign_role():
    name = "assign_role accepts primary_user (normalizes to admin)"
    if rm is None or roles is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        _reset()
        out = rm.assign_role("u-primary", "primary_user")  # type: ignore[union-attr]
        got = rm.get_user_role("u-primary")
        passed = out == roles.ROLE_ADMIN and got == roles.ROLE_ADMIN  # type: ignore[union-attr]
        _reset()
        print_result(name, "PASS" if passed else "FAIL", {"assigned": out, "lookup": got})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_caregiver_assign_and_lookup():
    name = "assign_role stores caregiver; get_user_role returns caregiver"
    if rm is None or roles is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        _reset()
        rm.assign_role("u-cg", roles.ROLE_CAREGIVER)  # type: ignore[union-attr]
        got = rm.get_user_role("u-cg")
        passed = got == roles.ROLE_CAREGIVER  # type: ignore[union-attr]
        _reset()
        print_result(name, "PASS" if passed else "FAIL", {"role": got})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_guest_denied_device_control_enforce():
    name = "enforce_permission denies DEVICE_CONTROL for guest with fake send_error"
    if rbac is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        _reset()
        rbac.assign_role("u-g", rbac.ROLE_GUEST)  # type: ignore[union-attr]
        errors = []

        def fake_se(sock, msg):
            errors.append(msg)

        ok = rbac.enforce_permission(  # type: ignore[union-attr]
            object(), "u-g", rbac.Permission.DEVICE_CONTROL, send_error=fake_se
        )
        passed = (ok is False) and len(errors) == 1 and "denied" in errors[0].lower()
        _reset()
        print_result(name, "PASS" if passed else "FAIL", {"ok": ok, "errors": errors})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_caregiver_allowed_scene_trigger_enforce():
    name = "enforce_permission allows SCENE_TRIGGER for caregiver"
    if rbac is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        _reset()
        rbac.assign_role("u-cg2", roles.ROLE_CAREGIVER)  # type: ignore[union-attr]
        errors = []

        def fake_se(sock, msg):
            errors.append(msg)

        ok = rbac.enforce_permission(  # type: ignore[union-attr]
            object(), "u-cg2", rbac.Permission.SCENE_TRIGGER, send_error=fake_se
        )
        passed = (ok is True) and not errors
        _reset()
        print_result(name, "PASS" if passed else "FAIL", None)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_device_access_servo_denied_caregiver():
    name = "infer servo/window type denied for caregiver control"
    if da is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        _reset()
        rm.assign_role("cg-s", roles.ROLE_CAREGIVER)  # type: ignore[union-attr]
        p = da.user_can_access_device("cg-s", "servo-1", "servo", need_control=True)  # type: ignore[union-attr]
        _reset()
        print_result(name, "PASS" if not p else "FAIL", {"allowed": p})
        return not p
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_device_access_smoke_sensor_allowed_caregiver():
    name = "smoke-typed device allowed for caregiver"
    if da is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        _reset()
        rm.assign_role("cg-sm", roles.ROLE_CAREGIVER)  # type: ignore[union-attr]
        a = da.user_can_access_device("cg-sm", "smoke-1", "smoke", need_control=True)  # type: ignore[union-attr]
        _reset()
        print_result(name, "PASS" if a else "FAIL", None)
        return a
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_filter_devices_mixed_roles():
    name = "filter_devices_for_user: family_member keeps door; caregiver drops it"
    if da is None or rm is None or roles is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        _reset()
        rows = [
            {"deviceId": "led-1", "deviceType": "led"},
            {"deviceId": "door-1", "deviceType": "door"},
        ]
        rm.assign_role("fm1", roles.ROLE_FAMILY_MEMBER)  # type: ignore[union-attr]
        rm.assign_role("cg1", roles.ROLE_CAREGIVER)  # type: ignore[union-attr]
        f1 = {r["deviceId"] for r in da.filter_devices_for_user("fm1", rows)}  # type: ignore[union-attr]
        f2 = {r["deviceId"] for r in da.filter_devices_for_user("cg1", rows)}  # type: ignore[union-attr]
        passed = f1 == {"led-1", "door-1"} and f2 == {"led-1"}
        _reset()
        print_result(name, "PASS" if passed else "FAIL", {"family": f1, "caregiver": f2})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_check_access_caregiver_device_control():
    name = "check_access: caregiver has DEVICE_CONTROL at permission layer"
    if rbac is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        _reset()
        rbac.assign_role("cgc", roles.ROLE_CAREGIVER)  # type: ignore[union-attr]
        ok = rbac.check_access("cgc", rbac.Permission.DEVICE_CONTROL)  # type: ignore[union-attr]
        _reset()
        print_result(name, "PASS" if ok else "FAIL", None)
        return ok
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_revoke_role_sets_guest():
    name = "revoke_role downgrades to guest"
    if rm is None or rbac is None or roles is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        _reset()
        rm.assign_role("u-rev", roles.ROLE_CAREGIVER)  # type: ignore[union-attr]
        rm.revoke_role("u-rev")
        got = rm.get_user_role("u-rev")
        passed = got == roles.ROLE_GUEST  # type: ignore[union-attr]
        _reset()
        print_result(name, "PASS" if passed else "FAIL", {"role": got})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def main():
    print("Running extended RBAC and device access tests...\n")
    if rbac is None:
        print(_trace)
        return
    tests = [
        test_caregiver_in_roles_table,
        test_primary_user_resolves_in_assign_role,
        test_caregiver_assign_and_lookup,
        test_guest_denied_device_control_enforce,
        test_caregiver_allowed_scene_trigger_enforce,
        test_device_access_servo_denied_caregiver,
        test_device_access_smoke_sensor_allowed_caregiver,
        test_filter_devices_mixed_roles,
        test_check_access_caregiver_device_control,
        test_revoke_role_sets_guest,
    ]
    passed = failed = skipped = 0
    for t in tests:
        try:
            r = t()
            if r is None:
                skipped += 1
            elif r:
                passed += 1
            else:
                failed += 1
        except Exception as exc:
            print_result(t.__name__, "FAIL", repr(exc))
            failed += 1
    n = len(tests)
    print(f"\nSummary: {passed} passed, {failed} failed, {skipped} skipped of {n}.")


if __name__ == "__main__":
    main()
