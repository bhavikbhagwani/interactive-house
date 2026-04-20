"""
Sensors and automation package (Iteration 4).

Adds support for a variety of sensors (motion, temperature, humidity,
door/window) and a lightweight automation engine that can fire device
actions when sensor readings satisfy user-defined rules.

Public API:

    from src.sensors_automation import (
        SensorType,
        SensorStatus,
        Sensor,
        MotionSensor,
        TemperatureSensor,
        HumiditySensor,
        DoorWindowSensor,
        create_sensor,
        SensorManager,
        Condition,
        Operator,
        AutomationRule,
        AutomationEngine,
        InvalidSensorDataError,
        SensorDisconnectedError,
    )
"""

from .sensors import (
    SensorType,
    SensorStatus,
    Sensor,
    MotionSensor,
    TemperatureSensor,
    HumiditySensor,
    DoorWindowSensor,
    create_sensor,
    InvalidSensorDataError,
    SensorDisconnectedError,
)
from .sensor_manager import SensorManager
from .automation import (
    Operator,
    Condition,
    AutomationRule,
    AutomationEngine,
)

__all__ = [
    "SensorType",
    "SensorStatus",
    "Sensor",
    "MotionSensor",
    "TemperatureSensor",
    "HumiditySensor",
    "DoorWindowSensor",
    "create_sensor",
    "SensorManager",
    "Operator",
    "Condition",
    "AutomationRule",
    "AutomationEngine",
    "InvalidSensorDataError",
    "SensorDisconnectedError",
]
