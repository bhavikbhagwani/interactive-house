# Sensors & Automation — Iteration 4

Adds sensor support and a small automation engine on top of the existing
device architecture.

## Sensors

Four sensor types are included; each one validates its own readings so
bad data from a noisy device is rejected without crashing the server.

| Type           | Value                                 |
| -------------- | ------------------------------------- |
| `motion`       | boolean (`True` = motion detected)    |
| `temperature`  | float Celsius, range `-50..80`        |
| `humidity`     | float percent, range `0..100`         |
| `door_window`  | `"open"` or `"closed"`                |

```python
from src.sensors_automation import SensorManager, SensorType

manager = SensorManager()
manager.register_new(SensorType.TEMPERATURE, "temp-living-room")
manager.connect("temp-living-room")
manager.ingest_reading("temp-living-room", 22.5)
```

Invalid readings (`"hot"`, `999`, `None`, ...) are dropped silently and
the sensor's `status` is set to `"error"` so the UI can show a warning.
Readings for a disconnected or unknown sensor id are also dropped.

## Automation rules

Rules bind a condition on a sensor to one or more device actions.

```python
from src.sensors_automation import (
    AutomationEngine, AutomationRule, Condition, Operator,
)

engine = AutomationEngine(
    sensor_manager=manager,
    action_dispatcher=lambda device_id, action: ...,
)

engine.add_rule(AutomationRule(
    rule_id="motion-light",
    condition=Condition("motion-hall", Operator.EQ, True),
    actions=[{"deviceId": "light-1", "action": "ON"}],
))
```

Every successful reading runs through every enabled rule. When a rule's
condition matches, the engine calls `action_dispatcher(device_id, action)`
for each action. In the server this dispatcher is a thin wrapper around
the existing `handle_action` pipeline, so automation flows through the
same code path as a manual button press from a unit client.

## Integration with the server

Wire once at startup (e.g. in `server.py`):

```python
from src.sensors_automation import SensorManager, AutomationEngine

sensor_manager = SensorManager()
automation_engine = AutomationEngine(
    sensor_manager=sensor_manager,
    action_dispatcher=dispatch_device_action,  # existing server helper
)
```

and forward any inbound sensor-data message to
`sensor_manager.ingest_reading(sensor_id, value)`.

## Package layout

```
server/src/sensors_automation/
├── __init__.py          # Public API re-exports
├── automation.py        # Condition / AutomationRule / AutomationEngine
├── sensor_manager.py    # Registry + reading dispatch
├── sensors.py           # Sensor base + motion/temp/humidity/door classes
└── README.md
```
