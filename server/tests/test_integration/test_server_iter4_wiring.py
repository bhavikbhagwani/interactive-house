"""Integration tests for serverService Iteration 4/5 (RBAC, scenes, voice paths).

Requires ``bcrypt`` and a working import of :mod:`serverService`.

Run (with optional live DB; uses in-memory role cache)::

    cd server
    python tests/test_integration/test_server_iter4_wiring.py
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from unittest.mock import patch

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
sys.path.insert(0, _SERVER_DIR)

try:
    import serverService as ss  # noqa: F401
except Exception as exc:
    ss = None
    _import_err = traceback.format_exc()
else:
    _import_err = ""


class _FakeSock:
    """Captures :func:`protocol.send_json` output (one message per call)."""

    def __init__(self):
        self.sent: list[bytes] = []

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)


def print_result(name, status, details=None):
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def _last_json(sock: _FakeSock) -> dict | None:
    if not sock.sent:
        return None
    line = sock.sent[-1].decode("utf-8").strip()
    return json.loads(line)


def _reset_roles_memory():
    try:
        from src.rbac import role_manager as rm  # type: ignore

        rm._db_available = lambda: False  # type: ignore[attr-defined]
        if hasattr(rm, "reset_memory_cache"):
            rm.reset_memory_cache()
    except Exception:
        pass


def test_caregiver_device_list_hides_door():
    name = "handle_get_devices filters out door for caregiver"
    if ss is None:
        print_result(
            name,
            "SKIP",
            _import_err.splitlines()[-1] if _import_err else "serverService import failed",
        )
        return None
    try:
        from src.rbac import role_manager as rm  # type: ignore
        from src.rbac import roles  # type: ignore

        _reset_roles_memory()
        rm._db_available = lambda: False  # type: ignore[attr-defined]
        uid = "42"
        rm.assign_role(uid, roles.ROLE_CAREGIVER)

        sock = _FakeSock()
        try:
            ss.unit_sockets[sock] = uid
            sample = [
                {"deviceId": "led-1", "deviceType": "led"},
                {"deviceId": "door-1", "deviceType": "door"},
            ]
            with patch.object(ss, "fetch_devices_list", return_value=sample):
                ss.handle_get_devices(sock)
            data = _last_json(sock)
            if not data or data.get("type") != "device_list":
                print_result(name, "FAIL", {"response": data})
                return False
            ids = {d["deviceId"] for d in data.get("payload", {}).get("devices", [])}
            passed = "led-1" in ids and "door-1" not in ids
            print_result(name, "PASS" if passed else "FAIL", {"ids": ids})
            return passed
        finally:
            ss.unit_sockets.pop(sock, None)
            _reset_roles_memory()
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_caregiver_cannot_run_good_night_scene():
    name = "handle_trigger_scene denies good_night for caregiver (door in scene)"
    if ss is None:
        print_result(name, "SKIP", "serverService import failed")
        return None
    try:
        from src.rbac import role_manager as rm  # type: ignore
        from src.rbac import roles  # type: ignore

        _reset_roles_memory()
        rm._db_available = lambda: False  # type: ignore[attr-defined]
        uid = "43"
        rm.assign_role(uid, roles.ROLE_CAREGIVER)

        sock = _FakeSock()
        try:
            ss.unit_sockets[sock] = uid
            ss.handle_trigger_scene(sock, "web-1", {"sceneId": "good_night"})
            data = _last_json(sock)
            msg = (data or {}).get("payload", {}).get("message", "")
            passed = (
                data is not None
                and data.get("type") == "error"
                and "denied" in msg.lower()
                and "door" in msg.lower()
            )
            print_result(
                name,
                "PASS" if passed else "FAIL",
                {"message": msg, "data": data},
            )
            return passed
        finally:
            ss.unit_sockets.pop(sock, None)
            _reset_roles_memory()
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_run_automation_motion_sends_on_to_leds():
    name = "run_automation_from_device_state turns on leds on motionDetected"
    if ss is None:
        print_result(name, "SKIP", "serverService import failed")
        return None
    try:
        led_sock = _FakeSock()
        saved = dict(ss.devices)
        try:
            ss.devices["led-1"] = {
                "socket": led_sock,
                "info": {"deviceType": "led"},
                "ui": [],
                "state": {},
            }
            ss.run_automation_from_device_state("motion-1", {"motionDetected": True})
            on_msgs = [json.loads(b.decode().strip()) for b in led_sock.sent]
            ok = any(
                m.get("type") == "action"
                and m.get("payload", {}).get("action") == "on"
                for m in on_msgs
            )
        finally:
            ss.devices.clear()
            ss.devices.update(saved)
        print_result(name, "PASS" if ok else "FAIL", {"led_messages": on_msgs})
        return ok
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def main():
    print("Running serverService Iter4 integration tests...\n")
    if ss is None:
        print("NOTE: serverService could not be imported. Install dependencies:\n  pip install -r requirements.txt\n")
        print(_import_err)
        return
    tests = [
        test_caregiver_device_list_hides_door,
        test_caregiver_cannot_run_good_night_scene,
        test_run_automation_motion_sends_on_to_leds,
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
