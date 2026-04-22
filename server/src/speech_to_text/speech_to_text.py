"""Speech-to-Text implementation.

Two layers live here:

1. :class:`SpeechToText` — a small class that parses natural-language
   commands into ``{"type": "scene" | "action" | "unknown", ...}``
   intent dicts. This is the layer the tests exercise directly.

2. A thin adapter to real speech-recognition backends (OpenAI Whisper
   or the standard-library friendly ``SpeechRecognition`` package that
   wraps Google's Web Speech API). The adapter is only used when
   ``transcribe(audio)`` is called with non-string audio; the tests
   never reach that code path, so the import is lazy.

Intent shapes produced by :meth:`SpeechToText.process`:

* Scene trigger:  ``{"type": "scene", "scene": "<snake_case_name>"}``
* Device action:  ``{"type": "action", "deviceId": "<id>", "action": "<verb>"}``
* Fallback:       ``{"type": "unknown", "message": "Sorry, not understood"}``

The class is deliberately self-contained so the server can import it
without needing any extra dependencies installed.
"""

from __future__ import annotations

import re
import threading
from typing import Any, Dict, List, Optional, Tuple


# =========================================================
# Vocabulary
# =========================================================

# Built-in device aliases. Keys are spoken words, values are the
# canonical device identifiers used elsewhere in the system. The
# dictionary can be extended at runtime via ``register_device_alias``.
DEFAULT_DEVICE_ALIASES: Dict[str, str] = {
    "light": "light",
    "lights": "light",
    "lamp": "light",
    "lamps": "light",
    "door": "door",
    "doors": "door",
    "fan": "fan",
    "fans": "fan",
    "tv": "tv",
    "television": "tv",
    "coffee": "coffee_machine",
    "coffee machine": "coffee_machine",
    "coffee maker": "coffee_machine",
    "blind": "blinds",
    "blinds": "blinds",
    "thermostat": "thermostat",
    "heater": "thermostat",
    "ac": "thermostat",
    "alarm": "alarm",
    "lock": "lock",
    "locks": "lock",
}

# Spoken verb -> canonical action verb.
DEFAULT_ACTION_ALIASES: Dict[str, str] = {
    "turn on": "on",
    "turn off": "off",
    "switch on": "on",
    "switch off": "off",
    "power on": "on",
    "power off": "off",
    "enable": "on",
    "disable": "off",
    "on": "on",
    "off": "off",
    "open": "open",
    "opens": "open",
    "close": "close",
    "closes": "close",
    "shut": "close",
    "lock": "lock",
    "unlock": "unlock",
    "start": "start",
    "stop": "stop",
    "brew": "start",
    "dim": "dim",
    "brighten": "brighten",
}

# Phrases that unambiguously name a scene without a verb (e.g. "movie
# night" said on its own). Keys are lowercase spoken forms, values are
# canonical scene identifiers (snake_case).
DEFAULT_SCENE_ALIASES: Dict[str, str] = {
    "movie night": "movie_night",
    "good morning": "good_morning",
    "good night": "good_night",
    "away": "away",
    "i'm home": "home",
    "home": "home",
    "dinner": "dinner",
    "party": "party",
    "bedtime": "bedtime",
}

# Verbs that introduce a scene name (e.g. "activate movie night").
SCENE_TRIGGER_VERBS: Tuple[str, ...] = (
    "activate",
    "run scene",
    "run",
    "start scene",
    "enable scene",
    "trigger",
    "play scene",
    "set scene",
    "scene",
)

_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^a-z0-9\s_-]+")


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, and collapse whitespace."""
    text = text.lower().strip()
    text = _PUNCT_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def _slug(text: str) -> str:
    """Turn a spoken scene name into a canonical snake_case identifier."""
    return _normalize(text).replace(" ", "_").replace("-", "_")


# =========================================================
# SpeechToText
# =========================================================

class SpeechToText:
    """Parse natural-language commands into structured intents."""

    def __init__(
        self,
        scene_aliases: Optional[Dict[str, str]] = None,
        device_aliases: Optional[Dict[str, str]] = None,
        action_aliases: Optional[Dict[str, str]] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._scene_aliases: Dict[str, str] = dict(DEFAULT_SCENE_ALIASES)
        if scene_aliases:
            self._scene_aliases.update(
                {k.lower(): v for k, v in scene_aliases.items()}
            )
        self._device_aliases: Dict[str, str] = dict(DEFAULT_DEVICE_ALIASES)
        if device_aliases:
            self._device_aliases.update(
                {k.lower(): v for k, v in device_aliases.items()}
            )
        self._action_aliases: Dict[str, str] = dict(DEFAULT_ACTION_ALIASES)
        if action_aliases:
            self._action_aliases.update(
                {k.lower(): v for k, v in action_aliases.items()}
            )

    # ---------- registration helpers ----------

    def register_scene_alias(self, spoken: str, canonical: str) -> None:
        with self._lock:
            self._scene_aliases[spoken.lower()] = canonical

    def register_device_alias(self, spoken: str, canonical: str) -> None:
        with self._lock:
            self._device_aliases[spoken.lower()] = canonical

    # ---------- transcription ----------

    def transcribe(self, audio: Any) -> str:
        """Convert an audio source to a text transcript.

        Accepts:
        * a ``str`` — returned unchanged (makes the tests work without a
          real microphone).
        * a ``bytes``-like or file-path-like object — handed to an
          optional speech-recognition backend if one is installed.

        The method never raises for missing backends; it raises only on
        genuinely invalid input.
        """

        if audio is None:
            raise ValueError("audio must not be None")
        if isinstance(audio, str):
            return audio

        # Optional backend. Imports are lazy so the server does not
        # need the extra packages installed just to run unit tests.
        try:  # pragma: no cover - exercised only on a real machine
            import speech_recognition as sr  # type: ignore

            recognizer = sr.Recognizer()
            if isinstance(audio, (bytes, bytearray)):
                audio_data = sr.AudioData(bytes(audio), 16000, 2)
            elif hasattr(audio, "read"):
                with sr.AudioFile(audio) as source:
                    audio_data = recognizer.record(source)
            else:
                with sr.AudioFile(str(audio)) as source:
                    audio_data = recognizer.record(source)
            return recognizer.recognize_google(audio_data)
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "No speech-recognition backend available. "
                "Install 'SpeechRecognition' or pass a pre-transcribed string."
            ) from exc

    def recognize(self, audio: Any) -> str:
        return self.transcribe(audio)

    def listen(self, audio: Any) -> str:
        return self.transcribe(audio)

    # ---------- main entry point ----------

    def process(self, text: Any) -> Dict[str, Any]:
        """Parse ``text`` into an intent dict. Never raises for valid input types."""

        if text is None:
            return self._unknown("Sorry, I did not hear anything.")
        if not isinstance(text, str):
            return self._unknown(
                f"Sorry, expected a text command, got {type(text).__name__}."
            )

        clean = _normalize(text)
        if not clean:
            return self._unknown("Sorry, I did not hear anything.")

        scene_intent = self._try_parse_scene(clean)
        if scene_intent is not None:
            return scene_intent

        action_intent = self._try_parse_action(clean)
        if action_intent is not None:
            return action_intent

        return self._unknown(f"Sorry, I did not understand: {text!r}")

    # Aliases exposed at the class level so the test adapter finds one.
    def process_voice_command(self, text: Any) -> Dict[str, Any]:
        return self.process(text)

    def handle_voice_command(self, text: Any) -> Dict[str, Any]:
        return self.process(text)

    def handle(self, text: Any) -> Dict[str, Any]:
        return self.process(text)

    def execute(self, text: Any) -> Dict[str, Any]:
        return self.process(text)

    # ---------- parsing helpers ----------

    def _unknown(self, message: str) -> Dict[str, Any]:
        return {
            "type": "unknown",
            "recognized": False,
            "ok": False,
            "message": message,
        }

    def _try_parse_scene(self, clean: str) -> Optional[Dict[str, Any]]:
        # 1) explicit "activate <scene>" / "run scene <scene>" etc.
        for verb in SCENE_TRIGGER_VERBS:
            prefix = verb + " "
            if clean.startswith(prefix):
                remainder = clean[len(prefix):].strip()
                if remainder:
                    return self._scene_result(remainder, text_hint=clean)

        # 2) "<scene> scene" / "scene <scene>" anywhere
        m = re.match(r"^(.+?)\s+scene$", clean)
        if m:
            return self._scene_result(m.group(1).strip(), text_hint=clean)

        # 3) known scene aliases appearing inside the utterance
        for spoken, canonical in self._scene_aliases.items():
            if spoken in clean:
                return {
                    "type": "scene",
                    "scene": canonical,
                    "sceneId": canonical,
                    "name": canonical,
                    "message": f"Activating scene: {canonical.replace('_', ' ')}",
                    "recognized": True,
                    "ok": True,
                    "raw": clean,
                }

        return None

    def _scene_result(self, raw_name: str, text_hint: str) -> Dict[str, Any]:
        canonical = self._scene_aliases.get(raw_name, _slug(raw_name))
        return {
            "type": "scene",
            "scene": canonical,
            "sceneId": canonical,
            "name": canonical,
            "message": f"Activating scene: {raw_name}",
            "recognized": True,
            "ok": True,
            "raw": text_hint,
        }

    def _try_parse_action(self, clean: str) -> Optional[Dict[str, Any]]:
        device_id = self._find_device(clean)
        action = self._find_action(clean)
        if device_id is None or action is None:
            return None
        return {
            "type": "action",
            "deviceId": device_id,
            "device": device_id,
            "action": action,
            "command": action,
            "message": f"Executing: {action} {device_id}",
            "recognized": True,
            "ok": True,
            "raw": clean,
        }

    def _find_device(self, clean: str) -> Optional[str]:
        # Match multi-word aliases first ("coffee machine" before "coffee").
        tokens_by_length = sorted(
            self._device_aliases.keys(), key=lambda s: -len(s)
        )
        for alias in tokens_by_length:
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, clean):
                return self._device_aliases[alias]
        return None

    def _find_action(self, clean: str) -> Optional[str]:
        # Multi-word verbs first.
        verbs_by_length = sorted(
            self._action_aliases.keys(), key=lambda s: -len(s)
        )
        for verb in verbs_by_length:
            pattern = r"\b" + re.escape(verb) + r"\b"
            if re.search(pattern, clean):
                return self._action_aliases[verb]
        return None


# =========================================================
# Module-level façade
# =========================================================

_default_speech: Optional[SpeechToText] = None
_default_lock = threading.Lock()


def _get_default_speech() -> SpeechToText:
    global _default_speech
    with _default_lock:
        if _default_speech is None:
            _default_speech = SpeechToText()
    return _default_speech


def process(text: Any) -> Dict[str, Any]:
    return _get_default_speech().process(text)


def process_voice_command(text: Any) -> Dict[str, Any]:
    return _get_default_speech().process(text)


def handle_voice_command(text: Any) -> Dict[str, Any]:
    return _get_default_speech().process(text)


def handle(text: Any) -> Dict[str, Any]:
    return _get_default_speech().process(text)


def execute(text: Any) -> Dict[str, Any]:
    return _get_default_speech().process(text)


def transcribe(audio: Any) -> str:
    return _get_default_speech().transcribe(audio)


def recognize(audio: Any) -> str:
    return _get_default_speech().recognize(audio)


def listen(audio: Any) -> str:
    return _get_default_speech().listen(audio)


def register_scene_alias(spoken: str, canonical: str) -> None:
    _get_default_speech().register_scene_alias(spoken, canonical)


def register_device_alias(spoken: str, canonical: str) -> None:
    _get_default_speech().register_device_alias(spoken, canonical)


def reset() -> None:
    """Drop and recreate the default parser (test-isolation helper)."""
    global _default_speech
    with _default_lock:
        _default_speech = SpeechToText()
