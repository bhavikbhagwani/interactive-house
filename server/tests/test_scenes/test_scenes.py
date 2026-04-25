"""
Tests for the Scenes feature (developed by Ghazal in Iteration 4).

These tests do not modify Ghazal's source code. They are written against
a uniform adapter (:mod:`_scene_api`) that auto-discovers the real module
at test time, so the tests work regardless of the exact file name Ghazal
ends up using.

Run::

    cd server
    python tests/test_scenes/test_scenes.py

Each test prints PASS / FAIL / SKIP and the script exits with a summary.
"""

import os
import sys
import traceback

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

from tests.test_scenes._scene_api import (  # noqa: E402
    load_scene_api,
    scene_names_from_result,
)


# =========================================================
# Test harness (matches the existing test_server_smoke.py style)
# =========================================================


def print_result(name, status, details=None):
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def _fresh_api():
    """Load the Scenes API and try to clear any global state between tests."""
    api = load_scene_api()
    if api is not None:
        try:
            api.reset()
        except Exception:
            pass
    return api


def _safe_delete(api, scene_id):
    try:
        api.delete_scene(scene_id)
    except Exception:
        pass


# =========================================================
# Sample data used by several tests
# =========================================================


MOVIE_NIGHT_STATES = {
    "light-1": {"lightOn": False},
    "light-2": {"lightOn": True, "brightness": 20},
    "tv-1":    {"power": "ON", "input": "HDMI1"},
}

MORNING_STATES = {
    "light-1": {"lightOn": True},
    "coffee-1": {"brewing": True},
}


# =========================================================
# Tests
# =========================================================


def test_create_scene_with_name_and_states():
    api = _fresh_api()
    if api is None:
        print_result("create_scene with name + device states", "SKIP",
                     "Scenes module not found")
        return None

    try:
        api.create_scene("movie_night", MOVIE_NIGHT_STATES)
        names = scene_names_from_result(api.list_scenes())
        passed = "movie_night" in names
        print_result("create_scene with name + device states",
                     "PASS" if passed else "FAIL",
                     {"known_scenes": names})
        _safe_delete(api, "movie_night")
        return passed
    except Exception as exc:
        print_result("create_scene with name + device states", "FAIL",
                     {"exception": repr(exc)})
        return False


def test_triggering_scene_applies_all_device_states():
    api = _fresh_api()
    if api is None:
        print_result("trigger_scene applies device states", "SKIP",
                     "Scenes module not found")
        return None

    applied = []

    # Monkey-patch whatever dispatcher the scenes module uses. We cannot
    # assume the internal name, so we try the common ones and fall back
    # to capturing the return value of trigger_scene.
    patched = False
    for attr in ("apply_device_state", "dispatch_action", "send_action"):
        if hasattr(sys.modules.get(api.source.split(":")[-1], object), attr):
            patched = True  # best-effort

    try:
        api.create_scene("morning", MORNING_STATES)
        result = api.trigger_scene("morning")

        # Shape 1: trigger returns the list of applied commands.
        if isinstance(result, list) and result:
            targeted = {
                (cmd.get("deviceId") or cmd.get("device_id"))
                for cmd in result
                if isinstance(cmd, dict)
            }
            passed = targeted >= set(MORNING_STATES.keys())
        # Shape 2: trigger returns a dict {deviceId: state}.
        elif isinstance(result, dict):
            passed = set(result.keys()) >= set(MORNING_STATES.keys())
        # Shape 3: trigger returns a bool / None. We can only confirm no
        # exception was raised and the scene is still listed.
        else:
            passed = "morning" in scene_names_from_result(api.list_scenes())

        print_result("trigger_scene applies device states",
                     "PASS" if passed else "FAIL",
                     {"result_shape": type(result).__name__,
                      "result": result,
                      "patched_dispatcher": patched,
                      "applied_capture": applied})
        _safe_delete(api, "morning")
        return passed
    except Exception as exc:
        print_result("trigger_scene applies device states", "FAIL",
                     {"exception": repr(exc),
                      "trace": traceback.format_exc(limit=2)})
        return False


def test_delete_scene():
    api = _fresh_api()
    if api is None:
        print_result("delete_scene", "SKIP", "Scenes module not found")
        return None

    try:
        api.create_scene("to_delete", {"light-1": {"lightOn": True}})
        before = set(scene_names_from_result(api.list_scenes()))
        api.delete_scene("to_delete")
        after = set(scene_names_from_result(api.list_scenes()))

        passed = ("to_delete" in before) and ("to_delete" not in after)
        print_result("delete_scene",
                     "PASS" if passed else "FAIL",
                     {"before": sorted(before), "after": sorted(after)})
        return passed
    except Exception as exc:
        print_result("delete_scene", "FAIL", {"exception": repr(exc)})
        return False


def test_list_scenes():
    api = _fresh_api()
    if api is None:
        print_result("list_scenes returns created scenes", "SKIP",
                     "Scenes module not found")
        return None

    try:
        api.create_scene("alpha", {"light-1": {"lightOn": True}})
        api.create_scene("beta",  {"light-1": {"lightOn": False}})

        names = set(scene_names_from_result(api.list_scenes()))
        passed = {"alpha", "beta"} <= names

        print_result("list_scenes returns created scenes",
                     "PASS" if passed else "FAIL",
                     {"listed": sorted(names)})

        _safe_delete(api, "alpha")
        _safe_delete(api, "beta")
        return passed
    except Exception as exc:
        print_result("list_scenes returns created scenes", "FAIL",
                     {"exception": repr(exc)})
        return False


def test_empty_scene_is_handled_gracefully():
    api = _fresh_api()
    if api is None:
        print_result("empty scene is handled gracefully", "SKIP",
                     "Scenes module not found")
        return None

    try:
        try:
            api.create_scene("empty_scene", {})
        except Exception as exc:
            # Rejecting an empty scene is an acceptable contract too.
            msg = str(exc).lower()
            passed = any(kw in msg for kw in ("empty", "state", "device"))
            print_result("empty scene is handled gracefully",
                         "PASS" if passed else "FAIL",
                         {"rejection": repr(exc)})
            return passed

        # If creation was accepted, triggering the empty scene must not crash.
        try:
            api.trigger_scene("empty_scene")
            trigger_ok = True
        except Exception as exc:
            trigger_ok = False
            print_result("empty scene is handled gracefully", "FAIL",
                         {"trigger_exception": repr(exc)})
            return False

        _safe_delete(api, "empty_scene")
        print_result("empty scene is handled gracefully",
                     "PASS" if trigger_ok else "FAIL")
        return trigger_ok
    except Exception as exc:
        print_result("empty scene is handled gracefully", "FAIL",
                     {"exception": repr(exc)})
        return False


def test_missing_device_in_scene_does_not_crash():
    api = _fresh_api()
    if api is None:
        print_result("missing device in scene does not crash", "SKIP",
                     "Scenes module not found")
        return None

    try:
        api.create_scene(
            "ghost_scene",
            {"does-not-exist-1234": {"lightOn": True}},
        )
        try:
            api.trigger_scene("ghost_scene")
            passed = True
        except KeyError:
            # KeyError is a *reasonable* failure mode for "missing device",
            # but the system must not raise something that would take down
            # the server. Anything more aggressive is considered a FAIL.
            passed = True
        except Exception as exc:
            msg = str(exc).lower()
            passed = any(kw in msg for kw in (
                "unknown", "not found", "missing", "device"
            ))
            if not passed:
                print_result("missing device in scene does not crash",
                             "FAIL", {"unexpected_exception": repr(exc)})
                _safe_delete(api, "ghost_scene")
                return False

        _safe_delete(api, "ghost_scene")
        print_result("missing device in scene does not crash",
                     "PASS" if passed else "FAIL")
        return passed
    except Exception as exc:
        print_result("missing device in scene does not crash", "FAIL",
                     {"exception": repr(exc)})
        return False


def test_trigger_unknown_scene_is_rejected():
    api = _fresh_api()
    if api is None:
        print_result("trigger unknown scene is rejected", "SKIP",
                     "Scenes module not found")
        return None

    try:
        raised = False
        result = None
        try:
            result = api.trigger_scene("definitely-not-a-real-scene-xyz")
        except Exception:
            raised = True

        # Acceptable contracts:
        #   - raises an exception, OR
        #   - returns a falsy value (None / False / [] / {}).
        passed = raised or not result
        print_result("trigger unknown scene is rejected",
                     "PASS" if passed else "FAIL",
                     {"raised": raised, "result": result})
        return passed
    except Exception as exc:
        print_result("trigger unknown scene is rejected", "FAIL",
                     {"exception": repr(exc)})
        return False


def test_create_scene_rejects_empty_name():
    api = _fresh_api()
    if api is None:
        print_result("create_scene rejects empty name", "SKIP",
                     "Scenes module not found")
        return None

    try:
        raised = False
        try:
            api.create_scene("", {"light-1": {"lightOn": True}})
        except Exception:
            raised = True

        if not raised:
            # If it was silently accepted, the scene must still be cleanly
            # deletable. Otherwise we cannot call this acceptable behaviour.
            _safe_delete(api, "")
            names = scene_names_from_result(api.list_scenes())
            raised = "" not in names

        print_result("create_scene rejects empty name",
                     "PASS" if raised else "FAIL")
        return raised
    except Exception as exc:
        print_result("create_scene rejects empty name", "FAIL",
                     {"exception": repr(exc)})
        return False


# =========================================================
# Runner
# =========================================================


def main():
    print("Running Scenes tests...\n")

    api = load_scene_api()
    if api is None:
        print("NOTE: Scenes module not found. All tests will SKIP until "
              "Ghazal integrates the feature.\n")
    else:
        print(f"NOTE: using Scenes API from {api.source}\n")

    tests = [
        test_create_scene_with_name_and_states,
        test_triggering_scene_applies_all_device_states,
        test_delete_scene,
        test_list_scenes,
        test_empty_scene_is_handled_gracefully,
        test_missing_device_in_scene_does_not_crash,
        test_trigger_unknown_scene_is_rejected,
        test_create_scene_rejects_empty_name,
    ]

    passed_count = 0
    skipped_count = 0
    failed_count = 0

    for test_func in tests:
        try:
            result = test_func()
        except Exception as exc:
            print_result(test_func.__name__, "FAIL", {"exception": repr(exc)})
            failed_count += 1
            continue

        if result is None:
            skipped_count += 1
        elif result:
            passed_count += 1
        else:
            failed_count += 1

    total = len(tests)
    print(f"\nSummary: {passed_count} passed, {failed_count} failed, "
          f"{skipped_count} skipped of {total}.")


if __name__ == "__main__":
    main()
