"""
Sensor type definitions for the smart home system.

Each sensor carries:
- a unique id
- a type (motion / temperature / humidity / door_window)
- a status (online / offline / error)
- a latest reading (validated per sensor type)
- a timestamp of the latest reading

Sensors are deliberately lightweight Python objects: they do not talk to
the network themselves. The real transport (TCP / hardware bridge) can
feed them through :class:`SensorManager.ingest_reading`.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional


# =========================================================
# ENUM-LIKE CONSTANTS
# =========================================================


class SensorType:
    """Supported sensor types. String values keep JSON serialisation easy."""

    MOTION = "motion"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    DOOR_WINDOW = "door_window"

    ALL = (MOTION, TEMPERATURE, HUMIDITY, DOOR_WINDOW)


class SensorStatus:
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


# =========================================================
# EXCEPTIONS
# =========================================================


class InvalidSensorDataError(ValueError):
    """Raised when a sensor reading fails validation for its type."""


class SensorDisconnectedError(RuntimeError):
    """Raised when trying to read from a sensor that is not online."""


# =========================================================
# BASE SENSOR
# =========================================================


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Sensor:
    """Base class for every sensor type.

    Subclasses override :meth:`_validate_value` to enforce per-type
    constraints. The base class is responsible for status tracking and
    graceful handling of disconnection / invalid data.
    """

    sensor_type: str = "generic"

    def __init__(self, sensor_id: str, name: Optional[str] = None):
        if not sensor_id or not isinstance(sensor_id, str):
            raise ValueError("sensor_id must be a non-empty string")
        self.sensor_id = sensor_id
        self.name = name or sensor_id
        self.status = SensorStatus.OFFLINE
        self.last_value: Any = None
        self.last_updated: Optional[str] = None
        self.last_error: Optional[str] = None

    # -- status management ---------------------------------------------

    def mark_online(self):
        self.status = SensorStatus.ONLINE
        self.last_error = None

    def mark_offline(self, reason: str = ""):
        self.status = SensorStatus.OFFLINE
        if reason:
            self.last_error = reason

    def mark_error(self, reason: str):
        self.status = SensorStatus.ERROR
        self.last_error = reason

    @property
    def is_connected(self) -> bool:
        return self.status == SensorStatus.ONLINE

    # -- reading ingestion ---------------------------------------------

    def update(self, value: Any) -> Any:
        """Validate and store a new reading.

        Raises :class:`SensorDisconnectedError` if the sensor is not
        currently online, or :class:`InvalidSensorDataError` if the
        validation for this sensor type rejects the value.
        """
        if self.status != SensorStatus.ONLINE:
            raise SensorDisconnectedError(
                f"Sensor {self.sensor_id} is {self.status}"
            )

        try:
            validated = self._validate_value(value)
        except InvalidSensorDataError:
            self.mark_error("invalid_data")
            raise
        except (TypeError, ValueError) as exc:
            self.mark_error("invalid_data")
            raise InvalidSensorDataError(str(exc)) from exc

        self.last_value = validated
        self.last_updated = _utc_now_iso()
        return validated

    def _validate_value(self, value: Any) -> Any:
        """Override in subclasses. Default: accept anything."""
        return value

    # -- serialisation -------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensorId": self.sensor_id,
            "name": self.name,
            "type": self.sensor_type,
            "status": self.status,
            "value": self.last_value,
            "lastUpdated": self.last_updated,
            "lastError": self.last_error,
        }

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.sensor_id!r} "
            f"status={self.status!r} value={self.last_value!r}>"
        )


# =========================================================
# CONCRETE SENSOR TYPES
# =========================================================


class MotionSensor(Sensor):
    """Binary motion sensor (``True`` = motion detected)."""

    sensor_type = SensorType.MOTION

    def _validate_value(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and value in (0, 1):
            return bool(value)
        if isinstance(value, str) and value.lower() in {
            "true", "false", "1", "0", "on", "off", "motion", "clear",
        }:
            return value.lower() in {"true", "1", "on", "motion"}
        raise InvalidSensorDataError(
            f"Motion sensor expects a boolean, got {value!r}"
        )


class TemperatureSensor(Sensor):
    """Temperature sensor (Celsius, -50..80 by default)."""

    sensor_type = SensorType.TEMPERATURE

    def __init__(
        self,
        sensor_id: str,
        name: Optional[str] = None,
        min_celsius: float = -50.0,
        max_celsius: float = 80.0,
    ):
        super().__init__(sensor_id, name)
        self.min_celsius = float(min_celsius)
        self.max_celsius = float(max_celsius)

    def _validate_value(self, value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise InvalidSensorDataError(
                f"Temperature must be numeric, got {value!r}"
            ) from exc
        if number != number:  # NaN check
            raise InvalidSensorDataError("Temperature reading is NaN")
        if not (self.min_celsius <= number <= self.max_celsius):
            raise InvalidSensorDataError(
                f"Temperature {number} outside allowed range "
                f"[{self.min_celsius}, {self.max_celsius}]"
            )
        return number


class HumiditySensor(Sensor):
    """Relative humidity sensor (percent, 0..100)."""

    sensor_type = SensorType.HUMIDITY

    def _validate_value(self, value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise InvalidSensorDataError(
                f"Humidity must be numeric, got {value!r}"
            ) from exc
        if not (0.0 <= number <= 100.0):
            raise InvalidSensorDataError(
                f"Humidity {number} outside 0..100"
            )
        return number


class DoorWindowSensor(Sensor):
    """Reed switch style sensor. State is ``"open"`` or ``"closed"``."""

    sensor_type = SensorType.DOOR_WINDOW

    _OPEN_ALIASES = {"open", "opened", "1", "true", "on"}
    _CLOSED_ALIASES = {"closed", "close", "shut", "0", "false", "off"}

    def _validate_value(self, value: Any) -> str:
        if isinstance(value, bool):
            return "open" if value else "closed"
        if isinstance(value, (int, float)) and value in (0, 1):
            return "open" if value == 1 else "closed"
        if isinstance(value, str):
            normalised = value.strip().lower()
            if normalised in self._OPEN_ALIASES:
                return "open"
            if normalised in self._CLOSED_ALIASES:
                return "closed"
        raise InvalidSensorDataError(
            f"Door/window sensor expects open/closed, got {value!r}"
        )


# =========================================================
# FACTORY
# =========================================================


_SENSOR_CLASSES = {
    SensorType.MOTION: MotionSensor,
    SensorType.TEMPERATURE: TemperatureSensor,
    SensorType.HUMIDITY: HumiditySensor,
    SensorType.DOOR_WINDOW: DoorWindowSensor,
}


def create_sensor(sensor_type: str, sensor_id: str, **kwargs) -> Sensor:
    """Build a sensor instance from a sensor type string."""
    if sensor_type not in _SENSOR_CLASSES:
        raise ValueError(f"Unknown sensor type: {sensor_type!r}")
    return _SENSOR_CLASSES[sensor_type](sensor_id, **kwargs)
