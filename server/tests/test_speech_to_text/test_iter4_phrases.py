"""Speech-to-text: Iteration 4/5 phrases (scenes, devices, server-style aliases).

Run::

    cd server
    python tests/test_speech_to_text/test_iter4_phrases.py
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
sys.path.insert(0, _SERVER_DIR)

from tests.test_speech_to_text._speech_api import load_speech_api  # noqa: E402


def print_result(name, status, details=None):
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def _register_iter4_aliases():
    from src.speech_to_text.speech_to_text import register_device_alias  # noqa: E402

    for spoken, did in (
        ("led", "led-1"),
        ("led one", "led-1"),
        ("led 1", "led-1"),
        ("light", "led-1"),
        ("fan", "fan-1"),
        ("door", "door-1"),
    ):
        try:
            register_device_alias(spoken, did)
        except Exception:
            pass


def test_good_night_and_good_morning_scenes():
    name = "good night / good morning map to scene intents"
    api = load_speech_api()
    if api is None:
        print_result(name, "SKIP", "speech API not found")
        return None
    try:
        n = api.process("good night")
        m = api.process("good morning")
        passed = bool(
            n.get("type") == "scene" and n.get("sceneId") == "good_night"
        ) and bool(
            m.get("type") == "scene" and m.get("sceneId") == "good_morning"
        )
        print_result(
            name,
            "PASS" if passed else "FAIL",
            {"night": n, "morning": m},
        )
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_led_one_with_server_aliases():
    name = "turn on led one resolves to device action (aliases like serverService)"
    api = load_speech_api()
    if api is None:
        print_result(name, "SKIP", "speech API not found")
        return None
    try:
        _register_iter4_aliases()
        r = api.process("turn on led one")
        passed = (
            r.get("type") == "action"
            and r.get("deviceId") == "led-1"
            and r.get("action") in ("on", "ON", "on")
        )
        print_result(name, "PASS" if passed else "FAIL", r)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_open_door_phrase():
    name = "open door maps to door-1 and open action"
    api = load_speech_api()
    if api is None:
        print_result(name, "SKIP", "speech API not found")
        return None
    try:
        _register_iter4_aliases()
        r = api.process("open door")
        passed = r.get("type") == "action" and r.get("deviceId") == "door-1" and r.get("action") == "open"
        print_result(name, "PASS" if passed else "FAIL", r)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def main():
    print("Running Iteration 4/5 speech phrase tests...\n")
    tests = [
        test_good_night_and_good_morning_scenes,
        test_led_one_with_server_aliases,
        test_open_door_phrase,
    ]
    passed = 0
    for t in tests:
        try:
            if t() is True:
                passed += 1
        except Exception as exc:
            print_result(t.__name__, "FAIL", repr(exc))
    print(f"\nSummary: {passed}/{len(tests)} tests passed.")


if __name__ == "__main__":
    main()
