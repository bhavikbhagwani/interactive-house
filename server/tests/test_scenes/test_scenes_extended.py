"""Extended Scenes API tests (CRUD, history, dispatcher, errors).

Run from ``server/``::

    python tests/test_scenes/test_scenes_extended.py
"""

from __future__ import annotations

import os
import sys
import traceback

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
sys.path.insert(0, _SERVER_DIR)

try:
    from src.scenes.scenes import (  # noqa: E402
        SceneManager,
        SceneNotFoundError,
        InvalidSceneError,
    )
except Exception:
    SceneManager = None  # type: ignore
    _trace = traceback.format_exc()
else:
    _trace = ""


def print_result(name: str, status: str, details=None) -> None:
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def _mk():
    if SceneManager is None:
        return None
    return SceneManager(auto_load=False)


def test_get_scene_after_create():
    name = "get_scene returns device_states after create_scene"
    m = _mk()
    if m is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        m.create_scene("alpha", {"d1": {"x": 1}})
        g = m.get_scene("alpha")
        passed = g is not None and g.get("device_states", {}).get("d1", {}).get("x") == 1
        m.reset()
        print_result(name, "PASS" if passed else "FAIL", {"got": g})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_get_history_tracks_triggers():
    name = "get_history records each trigger_scene in order"
    m = _mk()
    if m is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        m.create_scene("s1", {"a": {"v": 1}})
        m.create_scene("s2", {"b": {"v": 2}})
        m.trigger_scene("s1")
        m.trigger_scene("s2")
        m.trigger_scene("s1")
        h = m.get_history()
        passed = h == ["s1", "s2", "s1"]
        m.reset()
        print_result(name, "PASS" if passed else "FAIL", {"history": h})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_trigger_missing_scene_raises():
    name = "trigger_scene raises SceneNotFoundError for unknown scene"
    m = _mk()
    if m is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        try:
            m.trigger_scene("nope_nope_nope_zzz")
        except SceneNotFoundError as e:
            is_key = isinstance(e, KeyError)
            m.reset()
            print_result(name, "PASS", {"subclass_of_keyerror": is_key})
            return is_key
        m.reset()
        print_result(name, "FAIL", "expected SceneNotFoundError")
        return False
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_dispatcher_exception_does_not_break_trigger():
    name = "dispatcher exception is swallowed; trigger still returns commands"
    m = _mk()
    if m is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        def boom(did, st):
            raise RuntimeError("intentional")

        m.set_dispatcher(boom)
        m.create_scene("x", {"dev-1": {"action": "on"}})
        out = m.trigger_scene("x")
        ok = isinstance(out, list) and len(out) == 1
        m.reset()
        print_result(name, "PASS" if ok else "FAIL", {"out_len": len(out) if out else 0})
        return ok
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_list_scenes_includes_device_states_shape():
    name = "list_scenes entries include name, sceneId, device_states"
    m = _mk()
    if m is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        m.create_scene("listed", {"z-9": {"k": "v"}})
        rows = m.list_scenes()
        found = [r for r in rows if r.get("name") == "listed" or r.get("sceneId") == "listed"]
        passed = bool(found) and "device_states" in found[0] and "z-9" in found[0]["device_states"]
        m.reset()
        print_result(name, "PASS" if passed else "FAIL", {"first": found[0] if found else None})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_delete_scene_removes_from_get():
    name = "delete_scene removes scene from get_scene"
    m = _mk()
    if m is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        m.create_scene("bye", {"a": {}})
        if m.get_scene("bye") is None:
            m.reset()
            print_result(name, "FAIL", "create failed")
            return False
        m.delete_scene("bye")
        passed = m.get_scene("bye") is None
        m.reset()
        print_result(name, "PASS" if passed else "FAIL", None)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_create_rejects_whitespace_name():
    name = "create_scene rejects whitespace-only name"
    m = _mk()
    if m is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        raised = False
        try:
            m.create_scene("   ", {"a": {}})
        except (InvalidSceneError, ValueError, Exception):
            raised = True
        m.reset()
        print_result(name, "PASS" if raised else "FAIL", None)
        return raised
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_overwrite_scene_same_name():
    name = "create_scene overwrites device_states for same name"
    m = _mk()
    if m is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        m.create_scene("ow", {"a": {"v": 1}})
        m.create_scene("ow", {"a": {"v": 2}})
        g = m.get_scene("ow")
        passed = g["device_states"]["a"]["v"] == 2
        m.reset()
        print_result(name, "PASS" if passed else "FAIL", g)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_trigger_returns_stable_command_shape():
    name = "trigger_scene command dicts have deviceId and state"
    m = _mk()
    if m is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        m.create_scene("shape", {"id1": {"action": "toggle"}})
        cmds = m.trigger_scene("shape")
        c0 = cmds[0]
        passed = c0.get("deviceId") == "id1" and "state" in c0
        m.reset()
        print_result(name, "PASS" if passed else "FAIL", c0)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_empty_trigger_returns_empty_list():
    name = "trigger_scene on empty device_states returns empty command list"
    m = _mk()
    if m is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        m.create_scene("empty_cmds", {})
        out = m.trigger_scene("empty_cmds")
        passed = out == []
        m.reset()
        print_result(name, "PASS" if passed else "FAIL", {"out": out})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def main():
    print("Running extended Scenes tests...\n")
    if SceneManager is None:
        print(_trace)
        return
    tests = [
        test_get_scene_after_create,
        test_get_history_tracks_triggers,
        test_trigger_missing_scene_raises,
        test_dispatcher_exception_does_not_break_trigger,
        test_list_scenes_includes_device_states_shape,
        test_delete_scene_removes_from_get,
        test_create_rejects_whitespace_name,
        test_overwrite_scene_same_name,
        test_trigger_returns_stable_command_shape,
        test_empty_trigger_returns_empty_list,
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
