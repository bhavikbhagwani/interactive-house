"""Scenes: dispatcher receives device commands when scene uses action-shaped states.

Run::

    cd server
    python tests/test_scenes/test_scene_action_dispatch.py
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
sys.path.insert(0, _SERVER_DIR)

from tests.test_scenes._scene_api import load_scene_api  # noqa: E402


def print_result(name, status, details=None):
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def test_dispatcher_gets_on_off_actions():
    name = "trigger_scene calls dispatcher with (deviceId, state) for action dicts"
    api = load_scene_api()
    if api is None:
        print_result(name, "SKIP", "scene API not found")
        return None
    sm = None
    try:
        from src.scenes.scenes import SceneManager  # noqa: E402
    except Exception as exc:
        print_result(name, "SKIP", repr(exc))
        return None

    received = []

    def dispatch(device_id, state):
        received.append((device_id, state))

    try:
        sm = SceneManager(dispatcher=None, auto_load=False)
        sm.set_dispatcher(dispatch)
        sm.create_scene("test_scene_actions", {
            "led-1": {"action": "on"},
            "fan-1": {"action": "off"},
        })
        out = sm.trigger_scene("test_scene_actions")
        ok = len(received) == 2
        if isinstance(out, list) and len(out) >= 2:
            devs = {c.get("deviceId") for c in out if isinstance(c, dict)}
            ok = ok and devs >= {"led-1", "fan-1"}
        print_result(name, "PASS" if ok else "FAIL", {"received": received, "out": out})
        return ok
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False
    finally:
        try:
            if sm is not None:
                sm.delete_scene("test_scene_actions")
        except Exception:
            pass


def main():
    print("Running scene action dispatch tests...\n")
    r = test_dispatcher_gets_on_off_actions()
    print(f"\nSummary: {1 if r else 0}/1 tests passed.")


if __name__ == "__main__":
    main()
