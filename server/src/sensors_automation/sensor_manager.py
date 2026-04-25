"""
Registry that owns all live :class:`Sensor` objects and feeds readings
into the automation engine.
"""

from typing import Callable, Dict, List, Optional

from .sensors import (
    Sensor,
    SensorStatus,
    InvalidSensorDataError,
    SensorDisconnectedError,
    create_sensor,
)


class SensorManager:
    """Holds sensors keyed by id and dispatches readings."""

    def __init__(self):
        self._sensors: Dict[str, Sensor] = {}
        self._listeners: List[Callable[[Sensor, object], None]] = []

    # -- registration --------------------------------------------------

    def register(self, sensor: Sensor) -> Sensor:
        if sensor.sensor_id in self._sensors:
            raise ValueError(
                f"Sensor {sensor.sensor_id} is already registered"
            )
        self._sensors[sensor.sensor_id] = sensor
        return sensor

    def register_new(self, sensor_type: str, sensor_id: str, **kwargs) -> Sensor:
        """Convenience: build and register a sensor in one call."""
        sensor = create_sensor(sensor_type, sensor_id, **kwargs)
        return self.register(sensor)

    def unregister(self, sensor_id: str) -> Optional[Sensor]:
        return self._sensors.pop(sensor_id, None)

    def get(self, sensor_id: str) -> Optional[Sensor]:
        return self._sensors.get(sensor_id)

    def list_sensors(self) -> List[Sensor]:
        return list(self._sensors.values())

    # -- listeners (used by the automation engine) --------------------

    def add_listener(self, callback: Callable[[Sensor, object], None]):
        """Register a callback called on every successful reading."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[Sensor, object], None]):
        try:
            self._listeners.remove(callback)
        except ValueError:
            pass

    # -- lifecycle -----------------------------------------------------

    def connect(self, sensor_id: str):
        sensor = self._require(sensor_id)
        sensor.mark_online()

    def disconnect(self, sensor_id: str, reason: str = "manual"):
        """Mark a sensor offline without removing it.

        Keeps the sensor in the registry so historical readings and the
        "last seen" timestamp survive a temporary disconnect.
        """
        sensor = self._require(sensor_id)
        sensor.mark_offline(reason=reason)

    # -- reading ingestion --------------------------------------------

    def ingest_reading(self, sensor_id: str, value) -> Optional[object]:
        """Deliver a new reading to the matching sensor.

        Returns the validated value on success, or ``None`` if the sensor
        is unknown, disconnected, or the value is invalid. Errors are
        recorded on the sensor object rather than propagated so the caller
        (e.g. the TCP handler) never crashes on bad input.
        """
        sensor = self._sensors.get(sensor_id)
        if sensor is None:
            return None

        # Auto-connect on the first valid reading: devices can come online
        # without an explicit connect() call. Also auto-clear a transient
        # ERROR status so a single bad packet does not permanently mute
        # the sensor.
        if sensor.status in (SensorStatus.OFFLINE, SensorStatus.ERROR):
            sensor.mark_online()

        try:
            validated = sensor.update(value)
        except SensorDisconnectedError:
            return None
        except InvalidSensorDataError:
            return None

        for listener in list(self._listeners):
            try:
                listener(sensor, validated)
            except Exception:  # pragma: no cover - defensive
                # A broken listener must never take out the whole pipeline.
                pass

        return validated

    # -- internal ------------------------------------------------------

    def _require(self, sensor_id: str) -> Sensor:
        sensor = self._sensors.get(sensor_id)
        if sensor is None:
            raise KeyError(f"Unknown sensor: {sensor_id}")
        return sensor

    def snapshot(self) -> List[dict]:
        """Return a JSON-friendly snapshot of every sensor."""
        return [s.to_dict() for s in self._sensors.values()]
