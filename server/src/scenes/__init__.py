"""Scenes feature for the smart home system (Iteration 4, Ghazal).

A "scene" is a named preset that captures the desired state of one or
more devices. Triggering a scene applies all of its device states at
once, so a user can e.g. say "Movie Night" and have the lights dim,
the TV turn on, and the blinds close in a single action.

Public API (used by Sham's test adapter
``server/tests/test_scenes/_scene_api.py``):

* Module-level functions:
    - ``create_scene(name, device_states)``
    - ``trigger_scene(name)``
    - ``delete_scene(name)``
    - ``list_scenes()``
    - ``get_scene(name)``
    - ``reset()`` / ``clear()``  (test-isolation helpers)
    - ``get_history()``          (list of scene names that were triggered)

* ``SceneManager`` class with the same methods, usable without any
  arguments (the adapter instantiates it as ``SceneManager()``).

Persistence: scenes are stored as JSON in ``server/scenes.json`` so
they survive a server restart. The file lives alongside
``smart_home.db`` and is created lazily on the first write.
"""

from .scenes import (
    SceneManager,
    SceneError,
    SceneNotFoundError,
    InvalidSceneError,
    create_scene,
    trigger_scene,
    delete_scene,
    list_scenes,
    get_scene,
    reset,
    clear,
    get_history,
    set_dispatcher,
)

__all__ = [
    "SceneManager",
    "SceneError",
    "SceneNotFoundError",
    "InvalidSceneError",
    "create_scene",
    "trigger_scene",
    "delete_scene",
    "list_scenes",
    "get_scene",
    "reset",
    "clear",
    "get_history",
    "set_dispatcher",
]
