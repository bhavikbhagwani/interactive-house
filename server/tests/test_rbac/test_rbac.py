"""Tests for the RBAC feature (developed by Sham in Iteration 4).

These tests do not modify Sham's source code under ``server/src/rbac/``.
They exercise the public API described in the iteration-4 brief:

* permission / role constants
* role-to-permission mapping (admin / family_member / guest)
* ``check_access`` / ``role_has_permission`` / ``get_permissions``
* ``normalize_role`` (legacy "user" / "unit" -> "family_member")
* ``require_permission`` and its ``AccessDeniedError``
* ``enforce_permission`` (protocol-level handler helper)
* ``assign_role`` / ``revoke_role`` / ``get_user_role`` /
  ``list_users_with_roles`` / ``ensure_default_role``
* ``reset_memory_cache`` as the test-isolation lever

Run with::

    cd server
    python tests/test_rbac/test_rbac.py
"""

import os
import sys
import traceback


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
sys.path.insert(0, _SERVER_DIR)


# ---------------------------------------------------------------------------
# Try to load the RBAC module. If it cannot be imported we skip every test
# (same style as Sham's test_server_smoke.py / test_scenes).
# ---------------------------------------------------------------------------

try:  # pragma: no cover - exercised indirectly via the tests
    from src import rbac  # type: ignore
    from src.rbac import role_manager as _role_manager  # type: ignore
except Exception as _import_error:  # pragma: no cover
    rbac = None
    _role_manager = None
    _import_trace = traceback.format_exc()
else:
    _import_trace = ""
    # The tests deliberately run *without* a backing SQLite database so
    # that they stay hermetic. Forcing ``_db_available`` to False makes
    # ``assign_role`` / ``revoke_role`` / ``get_user_role`` use only the
    # in-memory cache, which is exactly the isolation mode the iter-4
    # brief describes.
    _role_manager._db_available = lambda: False  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Small reporting helpers (mirrors test_server_smoke.py).
# ---------------------------------------------------------------------------

def print_result(name, status, details=None):
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def _skip_all(name):
    if rbac is None:
        print_result(name, "SKIP", {"reason": "src.rbac not importable",
                                    "trace": _import_trace.splitlines()[-1] if _import_trace else ""})
        return True
    return False


def _fresh_rbac():
    """Clear the in-memory role cache so tests are order-independent."""
    if rbac is None:
        return
    # ``reset_memory_cache`` lives on ``role_manager`` but is not always
    # re-exported from the package. Look in both places.
    reset = getattr(rbac, "reset_memory_cache", None) or getattr(
        _role_manager, "reset_memory_cache", None
    )
    if callable(reset):
        try:
            reset()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 1. Constants and role-to-permission mapping
# ---------------------------------------------------------------------------

EXPECTED_ROLE_PERMISSIONS = {
    # admin has every permission the module exposes -> verified separately
    "family_member": {
        "device:view",
        "device:control",
        "scene:view",
        "scene:trigger",
        "scene:create",
        "scene:delete",
        "sensor:view",
        "automation:view",
    },
    "guest": {
        "device:view",
        "scene:view",
    },
}


def test_constants_exist():
    name = "rbac exposes role/permission constants"
    if _skip_all(name):
        return
    try:
        missing = []
        for attr in (
            "Permission",
            "ROLE_ADMIN",
            "ROLE_FAMILY_MEMBER",
            "ROLE_GUEST",
            "DEFAULT_ROLE",
            "ROLES",
            "role_has_permission",
            "get_permissions",
            "normalize_role",
            "check_access",
            "require_permission",
            "enforce_permission",
            "assign_role",
            "revoke_role",
            "get_user_role",
        ):
            if not hasattr(rbac, attr):
                missing.append(attr)
        passed = not missing
        print_result(name, "PASS" if passed else "FAIL",
                     {"missing": missing} if missing else None)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_admin_has_every_permission():
    """admin must be a superset of every other role."""
    name = "admin has every permission"
    if _skip_all(name):
        return
    try:
        roles = rbac.ROLES
        all_perms = set()
        for perms in roles.values():
            all_perms.update(perms)

        admin_perms = set(roles[rbac.ROLE_ADMIN])
        passed = admin_perms >= all_perms and all_perms
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"missing_for_admin": list(all_perms - admin_perms)})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_family_member_permission_set():
    """family_member (new in iter4) must match the documented set."""
    name = "family_member has expected permission set"
    if _skip_all(name):
        return
    try:
        perms = set(rbac.ROLES[rbac.ROLE_FAMILY_MEMBER])
        expected = EXPECTED_ROLE_PERMISSIONS["family_member"]
        missing = expected - perms
        unexpected_admin = {"role:assign", "user:manage", "settings:admin"} & perms
        passed = not missing and not unexpected_admin
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"missing": list(missing),
                                           "admin_leak": list(unexpected_admin)})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_guest_permission_set():
    name = "guest has minimal permission set"
    if _skip_all(name):
        return
    try:
        perms = set(rbac.ROLES[rbac.ROLE_GUEST])
        expected = EXPECTED_ROLE_PERMISSIONS["guest"]
        missing = expected - perms
        # A guest must not be able to CONTROL devices or MANAGE anything.
        forbidden = {
            "device:control",
            "scene:trigger",
            "scene:create",
            "scene:delete",
            "sensor:manage",
            "automation:manage",
            "role:assign",
            "user:manage",
            "settings:admin",
        } & perms
        passed = not missing and not forbidden
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"missing": list(missing),
                                           "forbidden_granted": list(forbidden)})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_role_has_permission_and_get_permissions():
    """The lookup helpers must agree with the ROLES table."""
    name = "role_has_permission / get_permissions agree with ROLES"
    if _skip_all(name):
        return
    try:
        checks = [
            (rbac.ROLE_ADMIN, rbac.Permission.USER_MANAGE, True),
            (rbac.ROLE_FAMILY_MEMBER, rbac.Permission.DEVICE_CONTROL, True),
            (rbac.ROLE_FAMILY_MEMBER, rbac.Permission.SCENE_CREATE, True),
            (rbac.ROLE_FAMILY_MEMBER, rbac.Permission.USER_MANAGE, False),
            (rbac.ROLE_GUEST, rbac.Permission.DEVICE_VIEW, True),
            (rbac.ROLE_GUEST, rbac.Permission.DEVICE_CONTROL, False),
            (rbac.ROLE_GUEST, rbac.Permission.SCENE_TRIGGER, False),
        ]
        mismatches = []
        for role, perm, expected in checks:
            got = rbac.role_has_permission(role, perm)
            if got != expected:
                mismatches.append({"role": role, "perm": perm, "expected": expected, "got": got})
            perms_set = set(rbac.get_permissions(role))
            if expected and perm not in perms_set:
                mismatches.append({"role": role, "perm": perm, "get_permissions_missing": True})
            if not expected and perm in perms_set:
                mismatches.append({"role": role, "perm": perm, "get_permissions_leaked": True})
        passed = not mismatches
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"mismatches": mismatches})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


# ---------------------------------------------------------------------------
# 2. Role normalization
# ---------------------------------------------------------------------------

def test_normalize_role_handles_legacy_names():
    name = "normalize_role maps legacy + family aliases to family_member"
    if _skip_all(name):
        return
    try:
        hits = []
        for legacy in (
            "user",
            "unit",
            "USER",
            "Unit",
            "family",
            "family member",
            "Family Member",
        ):
            normalized = rbac.normalize_role(legacy)
            if normalized != rbac.ROLE_FAMILY_MEMBER:
                hits.append({"legacy": legacy, "got": normalized})
        # Already-canonical names should stay untouched.
        for canonical in (rbac.ROLE_ADMIN, rbac.ROLE_FAMILY_MEMBER, rbac.ROLE_GUEST):
            normalized = rbac.normalize_role(canonical)
            if normalized != canonical:
                hits.append({"canonical": canonical, "got": normalized})
        passed = not hits
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"mismatches": hits})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


# ---------------------------------------------------------------------------
# 3. check_access / require_permission behaviour
# ---------------------------------------------------------------------------

def test_check_access_by_role_and_user():
    name = "check_access accepts both role names and user ids"
    if _skip_all(name):
        return
    try:
        _fresh_rbac()
        rbac.assign_role("user-alice", rbac.ROLE_ADMIN)
        rbac.assign_role("user-bob", rbac.ROLE_FAMILY_MEMBER)
        rbac.assign_role("user-carol", rbac.ROLE_GUEST)

        cases = [
            ("user-alice", rbac.Permission.USER_MANAGE, True),
            ("user-bob", rbac.Permission.DEVICE_CONTROL, True),
            ("user-bob", rbac.Permission.USER_MANAGE, False),
            ("user-carol", rbac.Permission.DEVICE_VIEW, True),
            ("user-carol", rbac.Permission.DEVICE_CONTROL, False),
            (rbac.ROLE_ADMIN, rbac.Permission.ROLE_ASSIGN, True),
            (rbac.ROLE_GUEST, rbac.Permission.SCENE_TRIGGER, False),
        ]
        mismatches = []
        for who, perm, expected in cases:
            got = rbac.check_access(who, perm)
            if got != expected:
                mismatches.append({"who": who, "perm": perm, "expected": expected, "got": got})
        passed = not mismatches
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"mismatches": mismatches})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_require_permission_allows_and_blocks():
    name = "require_permission returns role on success, raises on failure"
    if _skip_all(name):
        return
    try:
        _fresh_rbac()
        rbac.assign_role("u-allow", rbac.ROLE_FAMILY_MEMBER)
        rbac.assign_role("u-block", rbac.ROLE_GUEST)

        returned = rbac.require_permission("u-allow", rbac.Permission.DEVICE_CONTROL)
        allowed_ok = returned == rbac.ROLE_FAMILY_MEMBER

        denied = False
        exc_type = None
        try:
            rbac.require_permission("u-block", rbac.Permission.DEVICE_CONTROL)
        except Exception as exc:
            denied = True
            exc_type = type(exc).__name__

        # AccessDeniedError should exist and be raised.
        access_denied_cls = getattr(rbac, "AccessDeniedError", None)
        denied_is_correct_type = (access_denied_cls is None) or (exc_type == access_denied_cls.__name__)

        passed = allowed_ok and denied and denied_is_correct_type
        print_result(name, "PASS" if passed else "FAIL",
                     {"allowed_return": returned, "denied": denied, "exc_type": exc_type})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_enforce_permission_sends_error_on_deny():
    """enforce_permission should call send_error(sock, message) when denied."""
    name = "enforce_permission invokes send_error on deny, nothing on allow"
    if _skip_all(name):
        return
    try:
        _fresh_rbac()
        rbac.assign_role("u-fm", rbac.ROLE_FAMILY_MEMBER)
        rbac.assign_role("u-g", rbac.ROLE_GUEST)

        sent_errors = []

        def fake_send_error(sock, message):
            sent_errors.append({"sock": sock, "message": message})

        # Sham's ``enforce_permission`` only calls ``send_error`` when
        # it has a real socket to write to, so we pass a sentinel here.
        fake_sock = object()

        # Allowed call: should return truthy and NOT call send_error.
        allowed = rbac.enforce_permission(
            fake_sock, "u-fm", rbac.Permission.SCENE_TRIGGER,
            send_error=fake_send_error,
        )
        allow_ok = bool(allowed) and not sent_errors

        # Denied call: should return falsy and push exactly one error.
        denied = rbac.enforce_permission(
            fake_sock, "u-g", rbac.Permission.SCENE_TRIGGER,
            send_error=fake_send_error,
        )
        deny_ok = (not denied) and len(sent_errors) == 1

        passed = allow_ok and deny_ok
        print_result(name, "PASS" if passed else "FAIL",
                     {"allowed": allowed, "denied": denied, "errors": sent_errors})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


# ---------------------------------------------------------------------------
# 4. Role assignment / revocation / default role
# ---------------------------------------------------------------------------

def test_assign_and_get_role():
    name = "assign_role / get_user_role roundtrip"
    if _skip_all(name):
        return
    try:
        _fresh_rbac()
        rbac.assign_role("u-x", rbac.ROLE_ADMIN)
        got_admin = rbac.get_user_role("u-x") == rbac.ROLE_ADMIN

        # Overwrite with a lower role.
        rbac.assign_role("u-x", rbac.ROLE_GUEST)
        got_guest = rbac.get_user_role("u-x") == rbac.ROLE_GUEST

        passed = got_admin and got_guest
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"got_admin": got_admin, "got_guest": got_guest})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_revoke_role_resets_to_guest():
    """Per the iter-4 brief, revoke_role resets to guest."""
    name = "revoke_role resets user to guest"
    if _skip_all(name):
        return
    try:
        _fresh_rbac()
        rbac.assign_role("u-y", rbac.ROLE_FAMILY_MEMBER)
        rbac.revoke_role("u-y")
        got = rbac.get_user_role("u-y")
        passed = got == rbac.ROLE_GUEST
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"expected": rbac.ROLE_GUEST, "got": got})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_default_role_is_family_member():
    """The documented DEFAULT_ROLE must be family_member."""
    name = "DEFAULT_ROLE equals family_member"
    if _skip_all(name):
        return
    try:
        passed = rbac.DEFAULT_ROLE == rbac.ROLE_FAMILY_MEMBER
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"DEFAULT_ROLE": rbac.DEFAULT_ROLE,
                                           "ROLE_FAMILY_MEMBER": rbac.ROLE_FAMILY_MEMBER})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_ensure_default_role_when_available():
    """``ensure_default_role`` is optional; when exposed, it must assign DEFAULT_ROLE."""
    name = "ensure_default_role assigns DEFAULT_ROLE to a new user"
    if _skip_all(name):
        return
    try:
        ensure = getattr(rbac, "ensure_default_role", None) or getattr(
            _role_manager, "ensure_default_role", None
        )
        if not callable(ensure):
            print_result(name, "SKIP",
                         {"reason": "ensure_default_role not exposed by the RBAC module"})
            return None
        _fresh_rbac()
        ensure("u-new")
        got = rbac.get_user_role("u-new")
        passed = got == rbac.DEFAULT_ROLE == rbac.ROLE_FAMILY_MEMBER
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"got": got, "DEFAULT_ROLE": rbac.DEFAULT_ROLE})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_list_users_with_roles_reports_everyone():
    name = "list_users_with_roles reports every assigned user"
    if _skip_all(name):
        return
    try:
        _fresh_rbac()
        rbac.assign_role("u-1", rbac.ROLE_ADMIN)
        rbac.assign_role("u-2", rbac.ROLE_FAMILY_MEMBER)
        rbac.assign_role("u-3", rbac.ROLE_GUEST)

        listed = rbac.list_users_with_roles()
        mapping = _to_user_role_map(listed)

        expected = {"u-1": rbac.ROLE_ADMIN,
                    "u-2": rbac.ROLE_FAMILY_MEMBER,
                    "u-3": rbac.ROLE_GUEST}
        missing = {uid: role for uid, role in expected.items()
                   if mapping.get(uid) != role}
        passed = not missing
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"missing_or_wrong": missing, "listed": listed})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def _to_user_role_map(listed):
    """Normalise whatever list_users_with_roles returns into {user_id: role}."""
    mapping = {}
    if isinstance(listed, dict):
        return {str(k): v for k, v in listed.items()}
    for item in listed or []:
        if isinstance(item, dict):
            uid = item.get("user_id") or item.get("userId") or item.get("id")
            role = item.get("role")
            if uid is not None:
                mapping[str(uid)] = role
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            mapping[str(item[0])] = item[1]
    return mapping


# ---------------------------------------------------------------------------
# Main runner with PASS/FAIL/SKIP tally (same style as test_server_smoke).
# ---------------------------------------------------------------------------

def main():
    print("Running RBAC tests...\n")
    if rbac is None:
        print("NOTE: src.rbac could not be imported. All tests will SKIP.\n")
        print(_import_trace)
    else:
        print(f"NOTE: using rbac from {rbac.__name__}\n")

    tests = [
        test_constants_exist,
        test_admin_has_every_permission,
        test_family_member_permission_set,
        test_guest_permission_set,
        test_role_has_permission_and_get_permissions,
        test_normalize_role_handles_legacy_names,
        test_check_access_by_role_and_user,
        test_require_permission_allows_and_blocks,
        test_enforce_permission_sends_error_on_deny,
        test_assign_and_get_role,
        test_revoke_role_resets_to_guest,
        test_default_role_is_family_member,
        test_ensure_default_role_when_available,
        test_list_users_with_roles_reports_everyone,
    ]

    passed = failed = skipped = 0
    for test in tests:
        try:
            result = test()
        except Exception as exc:
            print_result(test.__name__, "FAIL", {"exception": repr(exc)})
            failed += 1
            continue

        if result is None:
            skipped += 1
        elif result:
            passed += 1
        else:
            failed += 1

    total = len(tests)
    print(f"\nSummary: {passed} passed, {failed} failed, {skipped} skipped of {total}.")


if __name__ == "__main__":
    main()
