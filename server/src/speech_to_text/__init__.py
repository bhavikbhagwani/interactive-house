"""Speech-to-Text feature for the smart home system (Iteration 4, Ghazal).

Users speak (or type) a command and the system turns it into either a
scene trigger ("activate movie night") or a device action ("turn off the
light"). Unrecognised phrases produce a clear fallback so the caller
can e.g. ask the user to repeat themselves.

Public API (matches the adapter at
``server/tests/test_speech_to_text/_speech_api.py``):

* ``process(text)`` / ``process_voice_command(text)`` — parse the
  transcript and return an intent dict (or a fallback dict).
* ``transcribe(audio)`` — best-effort audio-to-text hook. If a real
  speech recognition backend is available (Google Web Speech API,
  OpenAI Whisper) it is used; otherwise the function simply accepts an
  already-transcribed string.
* ``SpeechToText`` — zero-arg class exposing the same methods.

The design keeps the dependency on external speech-recognition
libraries optional so that unit tests never need network access.
"""

from .speech_to_text import (
    SpeechToText,
    process,
    process_voice_command,
    handle_voice_command,
    handle,
    execute,
    transcribe,
    recognize,
    listen,
    register_scene_alias,
    register_device_alias,
    reset,
)

__all__ = [
    "SpeechToText",
    "process",
    "process_voice_command",
    "handle_voice_command",
    "handle",
    "execute",
    "transcribe",
    "recognize",
    "listen",
    "register_scene_alias",
    "register_device_alias",
    "reset",
]
