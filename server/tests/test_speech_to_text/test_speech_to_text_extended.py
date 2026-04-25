"""Extended speech-to-text tests (intents, aliases, API surface, edge cases).

Run from ``server/``::

    python tests/test_speech_to_text/test_speech_to_text_extended.py
"""

from __future__ import annotations

import os
import sys
import traceback

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
sys.path.insert(0, _SERVER_DIR)

try:
    from src.speech_to_text.speech_to_text import SpeechToText, reset  # noqa: E402
except Exception:
    SpeechToText = None  # type: ignore
    reset = None  # type: ignore
    _trace = traceback.format_exc()
else:
    _trace = ""


def print_result(name: str, status: str, details=None) -> None:
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def _fresh() -> SpeechToText:
    if reset is not None:
        try:
            reset()
        except Exception:
            pass
    return SpeechToText()  # type: ignore[misc]


def test_process_voice_command_alias():
    name = "process_voice_command mirrors process for text str"
    if SpeechToText is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        st = _fresh()
        a = st.process("good night")
        b = st.process_voice_command("good night")
        passed = a == b
        print_result(name, "PASS" if passed else "FAIL", None)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_register_scene_alias_custom():
    name = "register_scene_alias maps custom phrase to scene id"
    if SpeechToText is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        st = _fresh()
        st.register_scene_alias("watch tv", "movie_night")
        r = st.process("watch tv")
        passed = r.get("type") == "scene" and r.get("sceneId") == "movie_night"
        print_result(name, "PASS" if passed else "FAIL", r)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_register_device_alias_custom():
    name = "register_device_alias maps phrase to device id"
    if SpeechToText is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        st = _fresh()
        st.register_device_alias("master bedroom lamp", "led-2")
        st.register_device_alias("turn on", "on")
        r = st.process("turn on master bedroom lamp")
        passed = r.get("type") == "action" and r.get("deviceId") == "led-2" and r.get("action") == "on"
        print_result(name, "PASS" if passed else "FAIL", r)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_spec_phrases_close_door_turn_off_fan():
    name = "close door; turn off fan (default aliases)"
    if SpeechToText is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        st = _fresh()
        c = st.process("close the door")
        f = st.process("turn off the fan")
        ok_c = c.get("type") == "action" and c.get("action") in ("close",) and "door" in str(c.get("deviceId", ""))
        ok_f = f.get("type") == "action" and f.get("action") in ("off",) and "fan" in str(f.get("deviceId", ""))
        passed = ok_c and ok_f
        print_result(name, "PASS" if passed else "FAIL", {"close_door": c, "fan": f})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_open_door_and_turn_on_led():
    name = "open door; turn on the light (device aliases)"
    if SpeechToText is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        st = _fresh()
        o = st.process("open the door")
        t = st.process("turn on the light")
        ok = (
            o.get("type") == "action" and o.get("action") == "open"
            and t.get("type") == "action" and t.get("action") == "on"
        )
        print_result(name, "PASS" if ok else "FAIL", {"open": o, "light": t})
        return ok
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_activate_scene_verb():
    name = "activate <scene> verb path resolves scene"
    if SpeechToText is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        st = _fresh()
        r = st.process("activate good morning")
        passed = r.get("type") == "scene" and "morning" in (r.get("sceneId") or "")
        print_result(name, "PASS" if passed else "FAIL", r)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_none_input_returns_unknown():
    name = "None text yields unknown / safe response"
    if SpeechToText is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        st = _fresh()
        r = st.process(None)  # type: ignore[arg-type]
        passed = r.get("type") == "unknown" or r.get("ok") is False
        print_result(name, "PASS" if passed else "FAIL", r)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_gibberish_unknown():
    name = "Random phrase returns unknown type"
    if SpeechToText is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        st = _fresh()
        r = st.process("quantum bramblefox z7")
        passed = r.get("type") == "unknown"
        print_result(name, "PASS" if passed else "FAIL", r)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_punctuation_stripped():
    name = "Punctuation in phrase still parses"
    if SpeechToText is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        st = _fresh()
        r = st.process("Good Night!!!")
        passed = r.get("type") == "scene" and r.get("sceneId") == "good_night"
        print_result(name, "PASS" if passed else "FAIL", r)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_module_level_process():
    name = "src.speech_to_text.process re-exports default parser"
    if SpeechToText is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        if reset is not None:
            reset()
        from src.speech_to_text import process  # noqa: E402
        r = process("good night")
        passed = r.get("type") == "scene" and r.get("sceneId") == "good_night"
        print_result(name, "PASS" if passed else "FAIL", r)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def main():
    print("Running extended speech-to-text tests...\n")
    if SpeechToText is None:
        print(_trace)
        return
    tests = [
        test_process_voice_command_alias,
        test_register_scene_alias_custom,
        test_register_device_alias_custom,
        test_spec_phrases_close_door_turn_off_fan,
        test_open_door_and_turn_on_led,
        test_activate_scene_verb,
        test_none_input_returns_unknown,
        test_gibberish_unknown,
        test_punctuation_stripped,
        test_module_level_process,
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
