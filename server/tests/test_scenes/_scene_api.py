"""
Adapter that locates Ghazal's Scenes feature at test-time.

The tests never modify Ghazal's source code, but they also do not know
its exact module path in advance. This adapter tries the most likely
locations and exposes a uniform API:

    api = load_scene_api()
    if api is None:
        # feature not integrated yet -> tests will be skipped
        ...
    api.create_scene(name, device_states)
    api.trigger_scene(name_or_id)
    api.delete_scene(name_or_id)
    api.list_scenes()
    api.get_scene(name_or_id)     # optional, may be None
    api.reset()                   # best-effort test-isolation helper

Supported integration shapes:

1. A module exposing top-level functions ``create_scene`` / ``trigger_scene``
   / ``delete_scene`` / ``list_scenes``.
2. A class ``SceneManager`` / ``ScenesService`` with the same method names,
   instantiated with no arguments.
"""

from __future__ import annotations

import importlib
import os
import sys
from types import SimpleNamespace
from typing import Any, Callable, Dict, List, Optional


# Make the server package importable when running this file directly.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)


_CANDIDATE_MODULES = (
    "scenes",
    "scene_service",
    "scene_manager",
    "src.scenes",
    "src.scene_service",
    "src.scene_manager",
    "src.scenes.scene_manager",
    "src.scenes.scenes",
)

_CANDIDATE_CLASSES = (
    "SceneManager",
    "ScenesService",
    "SceneService",
    "Scenes",
)

_FUNCTIONS = (
    "create_scene",
    "trigger_scene",
    "delete_scene",
    "list_scenes",
)


def _try_import(name: str):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def _wrap_module_functions(module) -> Optional[SimpleNamespace]:
    resolved: Dict[str, Callable[..., Any]] = {}
    for fn_name in _FUNCTIONS:
        fn = getattr(module, fn_name, None)
        if callable(fn):
            resolved[fn_name] = fn
    if len(resolved) < len(_FUNCTIONS):
        return None

    get_scene = getattr(module, "get_scene", None)
    reset = getattr(module, "reset", None) or getattr(module, "clear", None)

    return SimpleNamespace(
        source=f"module:{module.__name__}",
        create_scene=resolved["create_scene"],
        trigger_scene=resolved["trigger_scene"],
        delete_scene=resolved["delete_scene"],
        list_scenes=resolved["list_scenes"],
        get_scene=get_scene,
        reset=reset or (lambda: None),
    )


def _wrap_class_instance(module) -> Optional[SimpleNamespace]:
    for cls_name in _CANDIDATE_CLASSES:
        cls = getattr(module, cls_name, None)
        if cls is None:
            continue
        try:
            instance = cls()
        except TypeError:
            continue

        needed = [getattr(instance, name, None) for name in _FUNCTIONS]
        if any(m is None or not callable(m) for m in needed):
            continue

        get_scene = getattr(instance, "get_scene", None)
        reset = getattr(instance, "reset", None) or getattr(
            instance, "clear", None
        )

        return SimpleNamespace(
            source=f"class:{module.__name__}.{cls_name}",
            create_scene=instance.create_scene,
            trigger_scene=instance.trigger_scene,
            delete_scene=instance.delete_scene,
            list_scenes=instance.list_scenes,
            get_scene=get_scene,
            reset=reset or (lambda: None),
        )
    return None


def load_scene_api() -> Optional[SimpleNamespace]:
    """Return a uniform Scenes API or ``None`` if the feature is missing."""
    for mod_name in _CANDIDATE_MODULES:
        module = _try_import(mod_name)
        if module is None:
            continue

        api = _wrap_module_functions(module)
        if api is not None:
            return api

        api = _wrap_class_instance(module)
        if api is not None:
            return api

    return None


def scene_names_from_result(result: Any) -> List[str]:
    """Normalize the various shapes ``list_scenes`` might return."""
    if result is None:
        return []
    if isinstance(result, dict):
        return [str(k) for k in result.keys()]

    names: List[str] = []
    try:
        iterator = iter(result)
    except TypeError:
        return []

    for item in iterator:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict):
            for key in ("name", "sceneId", "scene_id", "id"):
                if key in item:
                    names.append(str(item[key]))
                    break
        else:
            for attr in ("name", "scene_id", "sceneId", "id"):
                value = getattr(item, attr, None)
                if value is not None:
                    names.append(str(value))
                    break
    return names
