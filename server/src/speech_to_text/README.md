# Speech-to-Text

Feature owner: Ghazal (Iteration 4).

Turns a spoken (or typed) natural-language command into a structured
intent that the rest of the system can act on.

```python
from src.speech_to_text import process

process("Activate Movie Night")
# {'type': 'scene', 'scene': 'movie_night', ...}

process("turn off the lights")
# {'type': 'action', 'deviceId': 'light', 'action': 'off', ...}

process("xyzzy plugh")
# {'type': 'unknown', 'recognized': False, 'ok': False,
#  'message': "Sorry, I did not understand: 'xyzzy plugh'"}
```

## Public API

* `process(text)` — main entry point. Also available as
  `process_voice_command`, `handle_voice_command`, `handle`, `execute`.
* `transcribe(audio)` — optional audio-to-text. A `str` is returned
  unchanged (great for tests); anything else tries to use the
  `SpeechRecognition` Python package if installed.
* `SpeechToText` — zero-arg class exposing the same methods.
* `register_scene_alias(spoken, canonical)` — add a new spoken phrase
  that names a scene (e.g. `"family time" -> "family_time"`).
* `register_device_alias(spoken, canonical)` — add a new device noun.
* `reset()` — recreate the default parser (used by tests for isolation).

## Intent shapes

| Intent  | Example payload                                              |
| ------- | ------------------------------------------------------------ |
| scene   | `{"type": "scene",   "scene": "movie_night", "ok": True}`    |
| action  | `{"type": "action",  "deviceId": "light", "action": "on"}`   |
| unknown | `{"type": "unknown", "recognized": False, "ok": False, ...}` |

## What the parser recognises out of the box

* **Scene triggers**: any of `activate`, `run scene`, `run`,
  `start scene`, `enable scene`, `trigger`, `play scene`, `set scene`,
  `scene` followed by a scene name — plus a handful of standalone
  aliases (`movie night`, `good morning`, `good night`, `away`,
  `dinner`, `party`, `bedtime`, ...).
* **Actions**: `turn on`, `turn off`, `switch on`, `switch off`,
  `power on`, `power off`, `enable`, `disable`, `open`, `close`,
  `shut`, `lock`, `unlock`, `start`, `stop`, `brew`, `dim`, `brighten`,
  and the bare words `on` / `off`.
* **Devices**: `light(s)`, `lamp(s)`, `door(s)`, `fan(s)`, `tv`,
  `television`, `coffee`, `coffee machine`, `coffee maker`, `blind(s)`,
  `thermostat`, `heater`, `ac`, `alarm`, `lock(s)`.

## Integrating with a real backend

```python
from src.speech_to_text import SpeechToText
stt = SpeechToText()

# In a client that receives audio bytes:
transcript = stt.transcribe(audio_bytes)     # uses SpeechRecognition if installed
intent = stt.process(transcript)
```

Both `openai-whisper` and `SpeechRecognition` work: the latter wraps
the Web Speech API behind a `recognize_google` call. Install one of
them only if you actually want audio support — the tests and the
default import path work without either.

## Robustness guarantees

* Case-insensitive and whitespace-insensitive: `"  TURN ON   the Light  "`
  is parsed the same way as `"turn on the light"`.
* Empty string, whitespace-only string and `None` never crash; they
  all yield the `"unknown"` fallback.
* Unrecognised input is *clearly* flagged (`type == "unknown"`,
  `recognized == False`, `ok == False`, message contains `"Sorry"`)
  so downstream callers can distinguish a real intent from a fallback.
