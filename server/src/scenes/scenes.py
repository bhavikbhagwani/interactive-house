"""Implementation of the Scenes feature.

The ``SceneManager`` class owns the in-memory collection of scenes and
knows how to persist it to ``server/scenes.json``. Module-level helpers
(``create_scene`` / ``trigger_scene`` / ...) delegate to a shared
default manager so callers can import either shape.
"""

from __future__ import annotations

import copy
import json
import os
import threading
from typing import Any, Callable, Dict, Iterable, List, Optional


# =========================================================
# Exceptions
# =========================================================

class SceneError(Exception):
    """Base class for scene-related errors."""


class SceneNotFoundError(SceneError, KeyError):
    """Raised when a scene name / id is unknown.

    Inherits from both :class:`SceneError` and :class:`KeyError` so that
    callers (including the integration test) may catch whichever flavour
    feels natural.
    """


class InvalidSceneError(SceneError, ValueError):
    """Raised when a scene definition is rejected (e.g. empty name)."""


# =========================================================
# Persistence helpers
# =========================================================

def _default_storage_path() -> str:
    # scenes.json sits next to smart_home.db inside the server/ folder.
    here = os.path.dirname(os.path.abspath(__file__))
    server_dir = os.path.abspath(os.path.join(here, os.pardir, os.pardir))
    return os.path.join(server_dir, "scenes.json")


# =========================================================
# SceneManager
# =========================================================

class SceneManager:
    """Owns the scene collection. Safe to use from multiple threads."""

    def __init__(
        self,
        storage_path: Optional[str] = None,
        dispatcher: Optional[Callable[[str, Any], None]] = None,
        auto_load: bool = True,
    ) -> None:
        self._storage_path = storage_path or _default_storage_path()
        self._scenes: Dict[str, Dict[str, Any]] = {}
        self._history: List[str] = []
        self._dispatcher: Optional[Callable[[str, Any], None]] = dispatcher
        self._lock = threading.RLock()

        if auto_load:
            try:
                self._load_from_disk()
            except Exception:
                # A corrupt scenes.json should not prevent startup; we
                # simply start with an empty collection.
                self._scenes = {}

    # ---------- internal helpers ----------

    @staticmethod
    def _normalize_name(name: Any) -> str:
        if not isinstance(name, str):
            raise InvalidSceneError(
                f"Scene name must be a string, got {type(name).__name__}"
            )
        stripped = name.strip()
        if not stripped:
            raise InvalidSceneError("Scene name must not be empty")
        return stripped

    def _load_from_disk(self) -> None:
        if not os.path.exists(self._storage_path):
            return
        with open(self._storage_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and isinstance(data.get("scenes"), dict):
            # {"scenes": {name: {device_states: {...}}}}
            self._scenes = {
                str(k): copy.deepcopy(v) for k, v in data["scenes"].items()
            }
        elif isinstance(data, dict):
            self._scenes = {str(k): copy.deepcopy(v) for k, v in data.items()}

    def _save_to_disk(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            with open(self._storage_path, "w", encoding="utf-8") as fh:
                json.dump({"scenes": self._scenes}, fh, indent=2, sort_keys=True)
        except OSError:
            # Persistence is best-effort: in a read-only test environment
            # we still want the in-memory operations to succeed.
            pass

    # ---------- public API ----------

    def set_dispatcher(
        self, dispatcher: Optional[Callable[[str, Any], None]]
    ) -> None:
        """Register a callback applied to every command of a triggered scene."""
        with self._lock:
            self._dispatcher = dispatcher

    def create_scene(
        self,
        name: str,
        device_states: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create (or overwrite) a scene.

        ``device_states`` is a mapping ``{deviceId: state_dict}``. An
        empty mapping is accepted (useful for building up a scene
        interactively) but an empty / non-string name is rejected.
        """

        key = self._normalize_name(name)

        if device_states is None:
            device_states = {}
        if not isinstance(device_states, dict):
            raise InvalidSceneError(
                "device_states must be a dict of deviceId -> state"
            )

        scene = {
            "name": key,
            "device_states": copy.deepcopy(device_states),
        }

        with self._lock:
            self._scenes[key] = scene
            self._save_to_disk()
            return copy.deepcopy(scene)

    def get_scene(self, name: str) -> Optional[Dict[str, Any]]:
        key = self._normalize_name(name)
        with self._lock:
            scene = self._scenes.get(key)
            return copy.deepcopy(scene) if scene is not None else None

    def list_scenes(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "name": s["name"],
                    "sceneId": s["name"],
                    "device_states": copy.deepcopy(s.get("device_states", {})),
                }
                for s in self._scenes.values()
            ]

    def delete_scene(self, name: str) -> bool:
        key = self._normalize_name(name)
        with self._lock:
            existed = self._scenes.pop(key, None) is not None
            if existed:
                self._save_to_disk()
            return existed

    def trigger_scene(self, name: str) -> List[Dict[str, Any]]:
        """Apply every device-state in the named scene.

        Returns a list of command dicts shaped as
        ``{"deviceId": ..., "state": ...}``. Unknown devices are still
        returned in the command list; dispatch failures do not bring
        down the server. A missing scene raises
        :class:`SceneNotFoundError`.
        """

        key = self._normalize_name(name)
        with self._lock:
            scene = self._scenes.get(key)
            if scene is None:
                raise SceneNotFoundError(f"Scene {key!r} not found")

            device_states = scene.get("device_states", {}) or {}
            self._history.append(key)
            dispatcher = self._dispatcher

        commands: List[Dict[str, Any]] = []
        for device_id, state in device_states.items():
            cmd = {
                "deviceId": device_id,
                "state": copy.deepcopy(state),
            }
            commands.append(cmd)
            if dispatcher is not None:
                try:
                    dispatcher(device_id, copy.deepcopy(state))
                except Exception:
                    # Never let a bad dispatcher crash the server.
                    pass
        return commands

    def get_history(self) -> List[str]:
        with self._lock:
            return list(self._history)

    def reset(self) -> None:
        """Drop every scene and the trigger history."""
        with self._lock:
            self._scenes = {}
            self._history = []
            try:
                if os.path.exists(self._storage_path):
                    os.remove(self._storage_path)
            except OSError:
                pass

    clear = reset


# =========================================================
# Module-level façade (shares one SceneManager)
# =========================================================

_default_manager: Optional[SceneManager] = None
_default_lock = threading.Lock()


def _get_default_manager() -> SceneManager:
    global _default_manager
    with _default_lock:
        if _default_manager is None:
            _default_manager = SceneManager()
    return _default_manager


def set_dispatcher(
    dispatcher: Optional[Callable[[str, Any], None]]
) -> None:
    _get_default_manager().set_dispatcher(dispatcher)


def create_scene(
    name: str, device_states: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return _get_default_manager().create_scene(name, device_states)


def trigger_scene(name: str) -> List[Dict[str, Any]]:
    return _get_default_manager().trigger_scene(name)


def delete_scene(name: str) -> bool:
    return _get_default_manager().delete_scene(name)


def list_scenes() -> List[Dict[str, Any]]:
    return _get_default_manager().list_scenes()


def get_scene(name: str) -> Optional[Dict[str, Any]]:
    return _get_default_manager().get_scene(name)


def get_history() -> List[str]:
    return _get_default_manager().get_history()


def reset() -> None:
    _get_default_manager().reset()


def clear() -> None:
    _get_default_manager().reset()
