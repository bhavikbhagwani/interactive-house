"""
Adapter that locates Ghazal's Speech-to-Text feature at test-time.

Tests never modify Ghazal's source code. They call a uniform façade so
they keep working no matter which module / class name she picks.

Usage::

    api = load_speech_api()
    if api is None:
        # feature not integrated yet -> test SKIPs
        ...
    outcome = api.process(text)       # feed a transcribed command
    text = api.transcribe(audio)      # optional, may be None

Supported integration shapes:

1. A module exposing top-level functions, any of:
   - ``process_voice_command(text)``
   - ``handle_voice_command(text)``
   - ``process(text)``
   - ``transcribe(audio)`` / ``recognize(audio)``
2. A class named ``SpeechToText`` / ``VoiceAssistant`` / ``VoiceService``
   with the same method names.
"""

from __future__ import annotations

import importlib
import os
import sys
from types import SimpleNamespace
from typing import Any, Callable, Optional


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)


_CANDIDATE_MODULES = (
    "speech_to_text",
    "stt",
    "voice",
    "voice_service",
    "src.speech_to_text",
    "src.stt",
    "src.voice",
    "src.voice_service",
    "src.speech_to_text.speech_to_text",
)

_CANDIDATE_CLASSES = (
    "SpeechToText",
    "VoiceAssistant",
    "VoiceService",
    "SpeechService",
    "STT",
)

_PROCESS_METHODS = (
    "process_voice_command",
    "handle_voice_command",
    "process",
    "handle",
    "execute",
)

_TRANSCRIBE_METHODS = (
    "transcribe",
    "recognize",
    "listen",
)


def _try_import(name: str):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def _first_callable(obj, names):
    for name in names:
        candidate = getattr(obj, name, None)
        if callable(candidate):
            return candidate, name
    return None, None


def _wrap(source_label: str, obj) -> Optional[SimpleNamespace]:
    process_fn, process_name = _first_callable(obj, _PROCESS_METHODS)
    if process_fn is None:
        return None

    transcribe_fn, transcribe_name = _first_callable(obj, _TRANSCRIBE_METHODS)

    return SimpleNamespace(
        source=source_label,
        process=process_fn,
        process_name=process_name,
        transcribe=transcribe_fn,
        transcribe_name=transcribe_name,
        raw=obj,
    )


def load_speech_api() -> Optional[SimpleNamespace]:
    """Return a uniform speech-to-text API or ``None`` if unavailable."""
    for mod_name in _CANDIDATE_MODULES:
        module = _try_import(mod_name)
        if module is None:
            continue

        wrapped = _wrap(f"module:{module.__name__}", module)
        if wrapped is not None:
            return wrapped

        for cls_name in _CANDIDATE_CLASSES:
            cls = getattr(module, cls_name, None)
            if cls is None:
                continue
            try:
                instance = cls()
            except TypeError:
                continue
            wrapped = _wrap(
                f"class:{module.__name__}.{cls_name}", instance
            )
            if wrapped is not None:
                return wrapped

    return None


def result_looks_like_scene_trigger(result: Any, scene_name: str) -> bool:
    """Best-effort inspection of the return value of ``process``.

    Different implementations return different shapes; this helper accepts
    anything that *clearly* references the expected scene.
    """
    if result is None:
        return False
    target = str(scene_name).lower().replace(" ", "_")

    if isinstance(result, str):
        return target in result.lower().replace(" ", "_")

    if isinstance(result, dict):
        # e.g. {"type": "scene", "scene": "movie_night"} or
        # {"action": "trigger_scene", "sceneId": "movie_night"}
        type_str = str(
            result.get("type")
            or result.get("action")
            or result.get("intent")
            or ""
        ).lower()
        target_str = str(
            result.get("scene")
            or result.get("sceneId")
            or result.get("scene_id")
            or result.get("name")
            or ""
        ).lower().replace(" ", "_")
        if "scene" in type_str and target_str == target:
            return True
        if target_str == target:
            return True
        # fall back: stringify everything and look for the scene name
        return target in str(result).lower().replace(" ", "_")

    return target in str(result).lower().replace(" ", "_")


def result_looks_like_device_action(
    result: Any, device_id: str = "", action: str = ""
) -> bool:
    """Best-effort: return True if ``result`` targets the given device/action."""
    if result is None:
        return False

    wanted_device = device_id.lower()
    wanted_action = action.lower()

    if isinstance(result, dict):
        actual_device = str(
            result.get("deviceId")
            or result.get("device_id")
            or result.get("device")
            or ""
        ).lower()
        actual_action = str(
            result.get("action")
            or result.get("command")
            or result.get("intent")
            or ""
        ).lower()
        device_ok = (not wanted_device) or wanted_device in actual_device
        action_ok = (not wanted_action) or wanted_action in actual_action
        return device_ok and action_ok

    text = str(result).lower()
    device_ok = (not wanted_device) or wanted_device in text
    action_ok = (not wanted_action) or wanted_action in text
    return device_ok and action_ok


def result_looks_like_unrecognized(result: Any) -> bool:
    """Return True if ``result`` represents a 'did not understand' fallback."""
    if result is None:
        return True
    if result is False:
        return True

    if isinstance(result, dict):
        type_str = str(
            result.get("type")
            or result.get("status")
            or result.get("intent")
            or ""
        ).lower()
        if any(kw in type_str for kw in (
            "unknown", "unrecognized", "fallback", "error", "none"
        )):
            return True
        if result.get("recognized") is False:
            return True
        if result.get("ok") is False:
            return True

    text = str(result).lower()
    return any(kw in text for kw in (
        "unknown", "unrecognized", "not understood", "sorry", "fallback"
    ))
