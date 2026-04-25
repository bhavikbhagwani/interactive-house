"""Sensors + automation: temperature threshold and smoke → alarm-style actions.

Run::

    cd server
    python tests/test_sensors_automation/test_temperature_smoke_rules.py
"""

from __future__ import annotations

import os
import sys
import traceback

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
sys.path.insert(0, _SERVER_DIR)

try:
    from src import sensors_automation as sa  # type: ignore
except Exception:
    sa = None
    _import_trace = traceback.format_exc()
else:
    _import_trace = ""


def print_result(name, status, details=None):
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def _skip(name):
    if sa is None:
        print_result(name, "SKIP", _import_trace.splitlines()[-1] if _import_trace else "import")
        return True
    return False


def test_high_temperature_triggers_fan():
    name = "temperature > threshold dispatches fan on"
    if _skip(name):
        return None
    try:
        manager = sa.SensorManager()
        engine = sa.AutomationEngine()
        engine.attach(manager)
        dispatched: list[tuple[str, str]] = []

        def dispatcher(device_id, action):
            dispatched.append((device_id, action))

        engine.set_dispatcher(dispatcher)
        manager.register_new(sa.SensorType.TEMPERATURE, "t-living", name="Living room")
        rule = sa.AutomationRule(
            rule_id="r-hot",
            name="fan on when hot",
            condition=sa.Condition(
                sensor_id="t-living",
                operator=sa.Operator.GT,
                value=28.0,
            ),
            actions=[{"deviceId": "fan-1", "action": "on"}],
        )
        engine.add_rule(rule)
        manager.ingest_reading("t-living", 22.0)
        no_fan = len(dispatched) == 0
        manager.ingest_reading("t-living", 30.0)
        fan_on = len(dispatched) == 1 and dispatched[0] == ("fan-1", "on")
        passed = no_fan and fan_on
        print_result(name, "PASS" if passed else "FAIL", {"dispatched": dispatched})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_smoke_boolean_triggers_alarm():
    name = "smoke / fire style reading dispatches alarm on (via motion-type bool path)"
    if _skip(name):
        return None
    try:
        manager = sa.SensorManager()
        engine = sa.AutomationEngine()
        engine.attach(manager)
        dispatched: list[str] = []

        def dispatcher(device_id, action):
            dispatched.append(f"{device_id}:{action}")

        engine.set_dispatcher(dispatcher)
        manager.register_new(sa.SensorType.MOTION, "smoke-sim", name="Kitchen smoke (simulated)")
        rule = sa.AutomationRule(
            rule_id="r-smoke",
            condition=sa.Condition(
                sensor_id="smoke-sim",
                operator=sa.Operator.EQ,
                value=True,
            ),
            actions=[{"deviceId": "alarm-1", "action": "on"}],
        )
        engine.add_rule(rule)
        manager.ingest_reading("smoke-sim", False)
        no_alarm = len(dispatched) == 0
        manager.ingest_reading("smoke-sim", True)
        alarm = len(dispatched) == 1 and "alarm-1" in dispatched[0]
        passed = no_alarm and alarm
        print_result(name, "PASS" if passed else "FAIL", {"dispatched": dispatched})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_more_sensors_mixed_manager():
    name = "SensorManager holds motion and temperature simultaneously"
    if _skip(name):
        return None
    try:
        manager = sa.SensorManager()
        manager.register_new(sa.SensorType.MOTION, "m-1", name="m")
        manager.register_new(sa.SensorType.TEMPERATURE, "t-1", name="t")
        manager.register_new(sa.SensorType.HUMIDITY, "h-1", name="h")
        m = manager.get("m-1")
        t = manager.get("t-1")
        passed = m is not None and t is not None and m.sensor_type == sa.SensorType.MOTION
        print_result(name, "PASS" if passed else "FAIL", None)
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def main():
    print("Running extra sensors + automation tests...\n")
    tests = [
        test_high_temperature_triggers_fan,
        test_smoke_boolean_triggers_alarm,
        test_more_sensors_mixed_manager,
    ]
    passed = 0
    for t in tests:
        try:
            if t() is True:
                passed += 1
        except Exception as exc:
            print_result(t.__name__, "FAIL", repr(exc))
    print(f"\nSummary: {passed}/{len(tests)} tests passed.")


if __name__ == "__main__":
    main()
