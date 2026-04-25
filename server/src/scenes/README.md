# Scenes

Feature owner: Ghazal (Iteration 4).

A **scene** is a named preset that captures a desired state for one or
more smart-home devices. Triggering a scene applies every device state
in a single action, so the user can say "Movie Night" and have the
lights dim, the TV switch on, and the thermostat adjust — all at once.

## Public API

```python
from src.scenes import (
    SceneManager,          # class, same methods as the module-level API
    create_scene,          # create (or overwrite) a scene
    trigger_scene,         # apply all device states in a scene
    delete_scene,          # remove a scene
    list_scenes,           # list every scene with its device states
    get_scene,             # fetch a single scene
    get_history,           # list scene names that were triggered (most recent last)
    set_dispatcher,        # plug in (device_id, state) -> None
    reset,                 # drop every scene (used for test isolation)
)
```

Scene commands produced by ``trigger_scene`` look like:

```json
[
  {"deviceId": "light-1", "state": {"lightOn": false, "brightness": 20}},
  {"deviceId": "light-2", "state": {"lightOn": false, "brightness": 20}},
  {"deviceId": "tv-1",    "state": {"power": "ON", "input": "HDMI1"}}
]
```

## Persistence

Scenes are stored as JSON in ``server/scenes.json`` next to
``smart_home.db``. The file is created lazily and a corrupt file is
treated as "no scenes" rather than a fatal error. Tests call
``SceneManager.reset()`` / ``reset()`` to clear both the in-memory
collection and the JSON file.

## Examples

```python
from src.scenes import create_scene, trigger_scene, delete_scene, list_scenes

create_scene("Movie Night", {
    "light-1": {"lightOn": False, "brightness": 20},
    "light-2": {"lightOn": False, "brightness": 20},
    "tv-1":    {"power": "ON", "input": "HDMI1"},
})

create_scene("Good Morning", {
    "light-1":  {"lightOn": True, "brightness": 80},
    "coffee-1": {"brewing": True},
})

trigger_scene("Movie Night")    # -> list of device commands
[s["name"] for s in list_scenes()]
# ['Movie Night', 'Good Morning']

delete_scene("Movie Night")
```

## Error behaviour

| Situation                                    | Result                         |
| -------------------------------------------- | ------------------------------ |
| ``create_scene("")`` / non-string name       | ``InvalidSceneError``          |
| ``create_scene(name, {})``                   | accepted, empty scene          |
| ``trigger_scene(name_not_found)``            | ``SceneNotFoundError``         |
| scene references an unknown deviceId         | command is still emitted; no crash |
| dispatcher raises an exception               | swallowed; remaining commands still dispatched |
