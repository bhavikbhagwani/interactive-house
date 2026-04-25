"""
Tests for the Speech-to-Text feature (developed by Ghazal, Iteration 4).

These tests do not modify Ghazal's source code. They talk to whatever
module she ends up shipping through the adapter in :mod:`_speech_api`.

Run::

    cd server
    python tests/test_speech_to_text/test_speech_to_text.py
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

from tests.test_speech_to_text._speech_api import (  # noqa: E402
    load_speech_api,
    result_looks_like_scene_trigger,
    result_looks_like_device_action,
    result_looks_like_unrecognized,
)


# =========================================================
# Harness (matches the existing test_server_smoke.py style)
# =========================================================


def print_result(name, status, details=None):
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def _skip_all(api, test_name):
    if api is None:
        print_result(test_name, "SKIP", "Speech-to-Text module not found")
        return True
    return False


# =========================================================
# Tests
# =========================================================


def test_voice_command_triggers_scene():
    api = load_speech_api()
    if _skip_all(api, "voice command triggers scene"):
        return None

    phrases = [
        "activate movie night",
        "start movie night",
        "movie night",
        "run scene movie night",
    ]

    last_result = None
    try:
        for phrase in phrases:
            last_result = api.process(phrase)
            if result_looks_like_scene_trigger(last_result, "movie_night"):
                print_result("voice command triggers scene", "PASS",
                             {"phrase": phrase, "result": last_result})
                return True

        print_result("voice command triggers scene", "FAIL",
                     {"phrases_tried": phrases, "last_result": last_result})
        return False
    except Exception as exc:
        print_result("voice command triggers scene", "FAIL",
                     {"exception": repr(exc)})
        return False


def test_voice_command_executes_device_action():
    api = load_speech_api()
    if _skip_all(api, "voice command executes device action"):
        return None

    # Match any device whose id contains 'light' and any ON-ish action.
    phrases = [
        "turn on the light",
        "light on",
        "switch on the light",
        "turn the light on",
    ]

    last_result = None
    try:
        for phrase in phrases:
            last_result = api.process(phrase)
            if result_looks_like_device_action(last_result, "light", "on"):
                print_result("voice command executes device action", "PASS",
                             {"phrase": phrase, "result": last_result})
                return True

        print_result("voice command executes device action", "FAIL",
                     {"phrases_tried": phrases, "last_result": last_result})
        return False
    except Exception as exc:
        print_result("voice command executes device action", "FAIL",
                     {"exception": repr(exc)})
        return False


def test_unrecognized_command_fallback():
    api = load_speech_api()
    if _skip_all(api, "unrecognized command fallback"):
        return None

    gibberish = [
        "flibber jibber wobble zoop",
        "xyzzy plugh",
        "blorptang the frangipani",
    ]

    try:
        results = []
        for phrase in gibberish:
            result = api.process(phrase)
            results.append(result)
            # Must NOT claim to have triggered a device or scene.
            if result_looks_like_device_action(result, "", "") and result:
                if not result_looks_like_unrecognized(result):
                    print_result("unrecognized command fallback", "FAIL",
                                 {"phrase": phrase,
                                  "result": result,
                                  "note": "recognized as action"})
                    return False

        # At least one gibberish phrase should be explicitly marked as
        # unrecognized / fallback. Being silently ignored (None / False) is
        # also acceptable.
        any_fallback = any(
            result_looks_like_unrecognized(r) for r in results
        )
        print_result("unrecognized command fallback",
                     "PASS" if any_fallback else "FAIL",
                     {"results": results})
        return any_fallback
    except Exception as exc:
        print_result("unrecognized command fallback", "FAIL",
                     {"exception": repr(exc)})
        return False


def test_case_and_whitespace_insensitivity():
    api = load_speech_api()
    if _skip_all(api, "case / whitespace insensitivity"):
        return None

    variants = [
        "Turn On The Light",
        "  turn   on the   light  ",
        "TURN ON THE LIGHT",
        "turn on the light",
    ]

    try:
        hits = 0
        for phrase in variants:
            result = api.process(phrase)
            if result_looks_like_device_action(result, "light", "on"):
                hits += 1

        # Being robust to at least one casing / whitespace variant besides
        # the canonical lowercase form is the minimum bar.
        passed = hits >= 2
        print_result("case / whitespace insensitivity",
                     "PASS" if passed else "FAIL",
                     {"variants": variants, "hits": hits})
        return passed
    except Exception as exc:
        print_result("case / whitespace insensitivity", "FAIL",
                     {"exception": repr(exc)})
        return False


def test_empty_input_does_not_crash():
    api = load_speech_api()
    if _skip_all(api, "empty input does not crash"):
        return None

    try:
        for bad in ("", "   ", None):
            try:
                result = api.process(bad)
            except TypeError:
                # Rejecting None with TypeError is acceptable; empty
                # string should not raise.
                if bad is None:
                    continue
                print_result("empty input does not crash", "FAIL",
                             {"input": repr(bad),
                              "note": "TypeError on empty string"})
                return False
            except ValueError:
                continue

            if result is not None and not result_looks_like_unrecognized(result):
                # An empty string that was "recognized" as a real action is
                # almost certainly a bug.
                if result_looks_like_device_action(result, "", "") and result:
                    print_result("empty input does not crash", "FAIL",
                                 {"input": repr(bad),
                                  "result": result,
                                  "note": "empty input triggered action"})
                    return False

        print_result("empty input does not crash", "PASS")
        return True
    except Exception as exc:
        print_result("empty input does not crash", "FAIL",
                     {"exception": repr(exc)})
        return False


def test_integration_between_speech_and_scene_layer():
    """Verify the speech layer actually reaches the scenes layer.

    When a real scenes module is present, triggering a scene via voice
    should either (a) put the scene in the list of triggered scenes, or
    (b) produce a result that clearly names the scene so the server can
    dispatch it. This mirrors the integration between layers.
    """
    api = load_speech_api()
    if _skip_all(api, "speech -> scenes integration"):
        return None

    try:
        # Try to import whatever scenes module exists, so we can inspect
        # real effects (optional). If missing, we fall back to inspecting
        # the process() return value only.
        try:
            from tests.test_scenes._scene_api import (
                load_scene_api, scene_names_from_result,
            )
            scene_api = load_scene_api()
        except Exception:
            scene_api = None
            scene_names_from_result = None  # noqa: N806

        scene_name = "good_night"
        created_here = False
        if scene_api is not None:
            try:
                scene_api.create_scene(
                    scene_name, {"light-1": {"lightOn": False}}
                )
                created_here = True
            except Exception:
                created_here = False

        result = api.process(f"activate {scene_name}")

        scene_referenced = result_looks_like_scene_trigger(result, scene_name)

        side_effect_ok = False
        if scene_api is not None:
            # Try to read any 'history' / 'last_triggered' exposed by the
            # scenes module. Optional: many implementations won't have this.
            history_fn = getattr(scene_api.raw if hasattr(scene_api, "raw")
                                 else None, "get_history", None)
            if callable(history_fn):
                try:
                    history = history_fn()
                    side_effect_ok = scene_name in str(history)
                except Exception:
                    side_effect_ok = False

        passed = scene_referenced or side_effect_ok

        if created_here and scene_api is not None:
            try:
                scene_api.delete_scene(scene_name)
            except Exception:
                pass

        print_result("speech -> scenes integration",
                     "PASS" if passed else "FAIL",
                     {"result": result,
                      "scene_api_present": scene_api is not None,
                      "scene_referenced": scene_referenced,
                      "side_effect_ok": side_effect_ok})
        return passed
    except Exception as exc:
        print_result("speech -> scenes integration", "FAIL",
                     {"exception": repr(exc)})
        return False


def test_integration_between_speech_and_device_layer():
    """A voice device command should produce a result aimed at a device."""
    api = load_speech_api()
    if _skip_all(api, "speech -> device integration"):
        return None

    try:
        phrases = [
            ("turn off the light", "light", "off"),
            ("open the door",      "door",  "open"),
            ("close the door",     "door",  "close"),
        ]

        hits = 0
        details = []
        for phrase, device_hint, action_hint in phrases:
            result = api.process(phrase)
            details.append({"phrase": phrase, "result": result})
            if result_looks_like_device_action(result, device_hint, action_hint):
                hits += 1

        passed = hits >= 1
        print_result("speech -> device integration",
                     "PASS" if passed else "FAIL",
                     {"hits": hits, "details": details})
        return passed
    except Exception as exc:
        print_result("speech -> device integration", "FAIL",
                     {"exception": repr(exc)})
        return False


# =========================================================
# Runner
# =========================================================


def main():
    print("Running Speech-to-Text tests...\n")

    api = load_speech_api()
    if api is None:
        print("NOTE: Speech-to-Text module not found. All tests will SKIP "
              "until Ghazal integrates the feature.\n")
    else:
        print(f"NOTE: using Speech-to-Text API from {api.source}\n")

    tests = [
        test_voice_command_triggers_scene,
        test_voice_command_executes_device_action,
        test_unrecognized_command_fallback,
        test_case_and_whitespace_insensitivity,
        test_empty_input_does_not_crash,
        test_integration_between_speech_and_scene_layer,
        test_integration_between_speech_and_device_layer,
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
