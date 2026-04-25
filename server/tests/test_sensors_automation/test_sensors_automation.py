"""Tests for the sensors + automation feature (developed by Sham, Iteration 4).

These tests do not modify Sham's source code under
``server/src/sensors_automation/``. They exercise the public API from
the iteration-4 brief:

* Every sensor type validates its own value range and rejects bad
  input. Either ``Sensor.update`` raises :class:`InvalidSensorDataError`
  directly, or ``SensorManager.ingest_reading`` swallows the error and
  returns ``None``.
* A disconnected sensor drops readings —
  :class:`SensorDisconnectedError` from ``Sensor.update``, ``None`` from
  ``SensorManager.ingest_reading``.
* ``AutomationRule`` fires its action dispatcher exactly when the
  attached condition matches, and never when the rule is disabled.
* Unknown sensor ids in ``SensorManager.ingest_reading`` are dropped
  silently (no exception, no listener callback).
* One bad packet does not permanently mute a sensor — the auto-clear
  of a transient ``ERROR`` state allows the next valid reading to be
  accepted.

Run with::

    cd server
    python tests/test_sensors_automation/test_sensors_automation.py
"""

import os
import sys
import traceback


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
sys.path.insert(0, _SERVER_DIR)


try:  # pragma: no cover - exercised via the tests themselves
    from src import sensors_automation as sa  # type: ignore
except Exception as _import_error:  # pragma: no cover
    sa = None
    _import_trace = traceback.format_exc()
else:
    _import_trace = ""


# ---------------------------------------------------------------------------
# Reporting helpers (same style as test_server_smoke.py).
# ---------------------------------------------------------------------------

def print_result(name, status, details=None):
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def _skip_all(name):
    if sa is None:
        print_result(name, "SKIP", {"reason": "src.sensors_automation not importable"})
        return True
    return False


# ---------------------------------------------------------------------------
# 1. Module surface
# ---------------------------------------------------------------------------

def test_public_surface_exists():
    name = "sensors_automation exposes the expected public API"
    if _skip_all(name):
        return
    try:
        missing = []
        for attr in (
            "SensorType", "SensorStatus", "Sensor", "MotionSensor",
            "TemperatureSensor", "HumiditySensor", "DoorWindowSensor",
            "create_sensor", "InvalidSensorDataError",
            "SensorDisconnectedError", "SensorManager",
            "Operator", "Condition", "AutomationRule", "AutomationEngine",
        ):
            if not hasattr(sa, attr):
                missing.append(attr)
        passed = not missing
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"missing": missing})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


# ---------------------------------------------------------------------------
# 2. Per-sensor-type value validation
# ---------------------------------------------------------------------------

def test_motion_sensor_validates_bool():
    name = "MotionSensor accepts bool, rejects non-bool"
    if _skip_all(name):
        return
    try:
        sensor = sa.MotionSensor(sensor_id="m-1", name="Hallway motion")
        sensor.mark_online()
        sensor.update(True)
        valid_ok = sensor.last_value is True

        raised = False
        try:
            sensor.update("maybe")
        except sa.InvalidSensorDataError:
            raised = True
        passed = valid_ok and raised
        print_result(name, "PASS" if passed else "FAIL",
                     {"valid_ok": valid_ok, "rejected_bad": raised})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def _online_temp_sensor(sensor_id="t-tmp", **kwargs):
    sensor = sa.TemperatureSensor(sensor_id=sensor_id, name=sensor_id, **kwargs)
    sensor.mark_online()
    return sensor


def _online_humidity_sensor(sensor_id="h-tmp"):
    sensor = sa.HumiditySensor(sensor_id=sensor_id, name=sensor_id)
    sensor.mark_online()
    return sensor


def _online_door_sensor(sensor_id="d-tmp"):
    sensor = sa.DoorWindowSensor(sensor_id=sensor_id, name=sensor_id)
    sensor.mark_online()
    return sensor


def test_temperature_sensor_respects_range():
    """Temperature sensor must accept values in the configured Celsius range and reject the rest.

    A fresh sensor is used per bad value because Sham's implementation
    drops a sensor into the ``ERROR`` state on the first invalid reading,
    and ``Sensor.update`` on an ERROR sensor raises
    :class:`SensorDisconnectedError`, not :class:`InvalidSensorDataError`.
    """
    name = "TemperatureSensor respects configurable min/max"
    if _skip_all(name):
        return
    try:
        sensor = _online_temp_sensor("t-good", min_celsius=-10, max_celsius=40)
        sensor.update(21.5)
        valid_ok = sensor.last_value == 21.5

        errors = []
        for i, bad in enumerate((-20, 41, "warm", float("nan"))):
            bad_sensor = _online_temp_sensor(
                f"t-bad-{i}", min_celsius=-10, max_celsius=40
            )
            try:
                bad_sensor.update(bad)
                errors.append({"value": bad, "accepted": True})
            except sa.InvalidSensorDataError:
                continue
            except Exception as exc:
                errors.append({"value": bad, "raised_wrong": type(exc).__name__})
        passed = valid_ok and not errors
        print_result(name, "PASS" if passed else "FAIL",
                     {"valid_ok": valid_ok, "unexpectedly_accepted": errors})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_humidity_sensor_bounds():
    name = "HumiditySensor bounds (0..100)"
    if _skip_all(name):
        return
    try:
        sensor = _online_humidity_sensor("h-good")
        sensor.update(55)
        valid_ok = sensor.last_value == 55

        rejected = 0
        for i, bad in enumerate((-1, 101, "dry")):
            bad_sensor = _online_humidity_sensor(f"h-bad-{i}")
            try:
                bad_sensor.update(bad)
            except sa.InvalidSensorDataError:
                rejected += 1
        passed = valid_ok and rejected == 3
        print_result(name, "PASS" if passed else "FAIL",
                     {"valid_ok": valid_ok, "rejected_count": rejected})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_door_window_sensor_accepts_open_closed():
    """The sensor accepts open/closed (and spelling aliases) and rejects everything else."""
    name = "DoorWindowSensor accepts 'open'/'closed', rejects other strings"
    if _skip_all(name):
        return
    try:
        sensor = _online_door_sensor("d-good")
        sensor.update("open")
        open_ok = sensor.last_value == "open"
        sensor.update("closed")
        valid_ok = open_ok and sensor.last_value == "closed"

        rejected = 0
        for i, bad in enumerate(("maybe", "slightly ajar", None)):
            bad_sensor = _online_door_sensor(f"d-bad-{i}")
            try:
                bad_sensor.update(bad)
            except sa.InvalidSensorDataError:
                rejected += 1
        passed = valid_ok and rejected == 3
        print_result(name, "PASS" if passed else "FAIL",
                     {"valid_ok": valid_ok, "rejected_count": rejected})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_create_sensor_factory_returns_correct_types():
    name = "create_sensor() factory returns the right subclass per type"
    if _skip_all(name):
        return
    try:
        pairs = [
            (sa.SensorType.MOTION, sa.MotionSensor),
            (sa.SensorType.TEMPERATURE, sa.TemperatureSensor),
            (sa.SensorType.HUMIDITY, sa.HumiditySensor),
            (sa.SensorType.DOOR_WINDOW, sa.DoorWindowSensor),
        ]
        mismatches = []
        for stype, cls in pairs:
            sensor = sa.create_sensor(stype, sensor_id=f"f-{stype}", name=f"factory-{stype}")
            if not isinstance(sensor, cls):
                mismatches.append({"type": stype, "expected": cls.__name__,
                                   "got": type(sensor).__name__})
        passed = not mismatches
        print_result(name, "PASS" if passed else "FAIL",
                     None if passed else {"mismatches": mismatches})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


# ---------------------------------------------------------------------------
# 3. Disconnection semantics
# ---------------------------------------------------------------------------

def test_disconnected_sensor_drops_direct_readings():
    """Calling ``Sensor.update`` directly on an offline sensor must raise.

    Note: the :class:`SensorManager` deliberately auto-reconnects an
    offline sensor on the first valid reading (see the iteration-4
    brief), so we exercise the direct path here and cover the manager
    path in :func:`test_ingest_reading_autoconnects_offline_sensor`.
    """
    name = "Offline Sensor.update raises SensorDisconnectedError"
    if _skip_all(name):
        return
    try:
        sensor = sa.MotionSensor(sensor_id="m-off", name="Garage motion")
        sensor.mark_offline("manual")
        raised = False
        exc_type = None
        try:
            sensor.update(True)
        except sa.SensorDisconnectedError as exc:
            raised = True
            exc_type = type(exc).__name__

        # A sensor moved into the ERROR state (e.g. bad hardware packet)
        # should behave the same way.
        err_sensor = sa.MotionSensor(sensor_id="m-err", name="Attic")
        err_sensor.mark_error("hardware fault")
        err_raised = False
        try:
            err_sensor.update(True)
        except sa.SensorDisconnectedError:
            err_raised = True

        passed = raised and err_raised and not sensor.is_connected
        print_result(name, "PASS" if passed else "FAIL",
                     {"offline_raised": raised, "error_raised": err_raised,
                      "exc_type": exc_type})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


# ---------------------------------------------------------------------------
# 4. SensorManager behaviour
# ---------------------------------------------------------------------------

def test_unknown_sensor_id_is_dropped_silently():
    name = "ingest_reading for an unknown sensor id is dropped silently"
    if _skip_all(name):
        return
    try:
        manager = sa.SensorManager()
        listener_hits = []
        manager.add_listener(lambda sensor, value: listener_hits.append((sensor, value)))
        result = manager.ingest_reading("does-not-exist", 42)
        passed = result is None and not listener_hits
        print_result(name, "PASS" if passed else "FAIL",
                     {"result": result, "listener_hits": listener_hits})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_ingest_reading_autoconnects_offline_sensor():
    name = "ingest_reading auto-connects an OFFLINE sensor on first valid reading"
    if _skip_all(name):
        return
    try:
        manager = sa.SensorManager()
        sensor = sa.TemperatureSensor(sensor_id="t-auto", name="Outside")
        manager.register(sensor)
        manager.disconnect("t-auto")

        result = manager.ingest_reading("t-auto", 19.5)
        passed = result == 19.5 and sensor.is_connected
        print_result(name, "PASS" if passed else "FAIL",
                     {"result": result, "is_connected": sensor.is_connected,
                      "status": getattr(sensor, "status", None)})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_bad_packet_does_not_permanently_mute_sensor():
    """A single invalid reading sets ERROR; the next valid reading clears it."""
    name = "one bad packet does not permanently mute a sensor"
    if _skip_all(name):
        return
    try:
        manager = sa.SensorManager()
        sensor = sa.HumiditySensor(sensor_id="h-mute", name="Crawlspace")
        manager.register(sensor)

        # First, a good reading so the sensor is online.
        manager.ingest_reading("h-mute", 40)
        # Now a bad packet.
        first_bad = manager.ingest_reading("h-mute", 9001)
        bad_was_dropped = first_bad is None
        # A second valid reading must succeed even though the previous
        # packet may have flipped the sensor into ERROR.
        recovered = manager.ingest_reading("h-mute", 45)
        passed = bad_was_dropped and recovered == 45
        print_result(name, "PASS" if passed else "FAIL",
                     {"bad_dropped": bad_was_dropped, "recovered": recovered,
                      "status": getattr(sensor, "status", None)})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_sensor_manager_listeners_receive_valid_readings():
    name = "SensorManager listeners receive a callback per valid reading"
    if _skip_all(name):
        return
    try:
        manager = sa.SensorManager()
        sensor = manager.register_new(sa.SensorType.MOTION, "m-listen", name="Office")
        hits = []

        def listener(sensor_obj, value):
            hits.append({"id": sensor_obj.sensor_id, "value": value})

        manager.add_listener(listener)
        manager.ingest_reading("m-listen", True)
        manager.ingest_reading("m-listen", False)
        # Remove the listener - further readings must not fire it.
        manager.remove_listener(listener)
        manager.ingest_reading("m-listen", True)

        passed = len(hits) == 2 and all(h["id"] == "m-listen" for h in hits)
        print_result(name, "PASS" if passed else "FAIL", {"hits": hits})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


# ---------------------------------------------------------------------------
# 5. AutomationRule / AutomationEngine behaviour
# ---------------------------------------------------------------------------

def test_automation_rule_fires_on_match():
    """The engine calls the dispatcher with ``(device_id, action)`` per matching rule."""
    name = "AutomationRule fires dispatcher exactly when condition matches"
    if _skip_all(name):
        return
    try:
        manager = sa.SensorManager()
        engine = sa.AutomationEngine()
        engine.attach(manager)

        dispatched = []

        def dispatcher(device_id, action):
            dispatched.append({"deviceId": device_id, "action": action})

        engine.set_dispatcher(dispatcher)

        manager.register_new(sa.SensorType.MOTION, "m-auto", name="Entry")

        rule = sa.AutomationRule(
            rule_id="rule-1",
            name="Lights on when motion",
            condition=sa.Condition(sensor_id="m-auto",
                                    operator=sa.Operator.EQ,
                                    value=True),
            actions=[{"deviceId": "light-entry", "action": "on"}],
        )
        engine.add_rule(rule)

        # No match: value is False -> no fire.
        manager.ingest_reading("m-auto", False)
        no_fire_ok = len(dispatched) == 0

        # Match: value True -> should fire exactly once.
        manager.ingest_reading("m-auto", True)
        fired_once = (len(dispatched) == 1
                      and dispatched[-1]["deviceId"] == "light-entry"
                      and dispatched[-1]["action"] == "on")

        # The rule's own counters should reflect the single firing.
        rule_counts_ok = rule.trigger_count == 1 and rule.last_triggered is not None

        passed = no_fire_ok and fired_once and rule_counts_ok
        print_result(name, "PASS" if passed else "FAIL",
                     {"dispatched": dispatched, "no_fire_ok": no_fire_ok,
                      "fired_once": fired_once,
                      "trigger_count": rule.trigger_count})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_disabled_rule_does_not_fire():
    name = "Disabled AutomationRule does not fire"
    if _skip_all(name):
        return
    try:
        manager = sa.SensorManager()
        engine = sa.AutomationEngine()
        engine.attach(manager)
        dispatched = []
        engine.set_dispatcher(lambda d, a: dispatched.append((d, a)))

        manager.register_new(sa.SensorType.HUMIDITY, "h-rule", name="Bath")
        rule = sa.AutomationRule(
            rule_id="r-hum",
            condition=sa.Condition(sensor_id="h-rule",
                                    operator=sa.Operator.GT,
                                    value=80),
            actions=[{"deviceId": "fan-1", "action": "on"}],
        )
        engine.add_rule(rule)

        # Rule enabled: crossing the threshold fires exactly once.
        manager.ingest_reading("h-rule", 85)
        fired_enabled = len(dispatched) == 1

        # Disable and re-fire: must NOT increase the count.
        engine.set_rule_enabled("r-hum", False)
        manager.ingest_reading("h-rule", 95)
        still_one = len(dispatched) == 1

        # Re-enable: fires again on the next matching reading.
        engine.set_rule_enabled("r-hum", True)
        manager.ingest_reading("h-rule", 90)
        fires_again = len(dispatched) == 2

        passed = fired_enabled and still_one and fires_again
        print_result(name, "PASS" if passed else "FAIL",
                     {"dispatched": dispatched, "fired_enabled": fired_enabled,
                      "still_one": still_one, "fires_again": fires_again})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_engine_tolerates_broken_dispatcher():
    """A dispatcher that raises must not take the engine down."""
    name = "AutomationEngine keeps running when dispatcher raises"
    if _skip_all(name):
        return
    try:
        manager = sa.SensorManager()
        engine = sa.AutomationEngine(sensor_manager=manager)

        calls = {"count": 0}

        def bad_dispatcher(device_id, action):
            calls["count"] += 1
            raise RuntimeError("boom")

        engine.set_dispatcher(bad_dispatcher)

        manager.register_new(sa.SensorType.TEMPERATURE, "t-rule", name="Fridge")
        rule = sa.AutomationRule(
            rule_id="r-cold",
            condition=sa.Condition(sensor_id="t-rule",
                                    operator=sa.Operator.LT,
                                    value=5),
            actions=[
                {"deviceId": "fridge", "action": "alarm"},
                {"deviceId": "phone", "action": "notify"},
            ],
        )
        engine.add_rule(rule)

        # Match. The dispatcher will raise; the engine must not propagate.
        survived = True
        try:
            manager.ingest_reading("t-rule", 1)
        except Exception:
            survived = False

        # The engine attempts every action even if earlier ones raised,
        # so we expect two dispatcher calls for this 2-action rule.
        passed = survived and calls["count"] == 2
        print_result(name, "PASS" if passed else "FAIL",
                     {"survived": survived, "dispatcher_calls": calls["count"]})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


def test_evaluate_returns_triggered_rules():
    """AutomationEngine.evaluate returns the rules that matched a reading."""
    name = "AutomationEngine.evaluate returns triggered rules"
    if _skip_all(name):
        return
    try:
        engine = sa.AutomationEngine()
        sensor = sa.DoorWindowSensor(sensor_id="d-eval", name="Back door")
        sensor.mark_online()

        rule_open = sa.AutomationRule(
            rule_id="r-open",
            condition=sa.Condition(sensor_id="d-eval",
                                    operator=sa.Operator.EQ,
                                    value="open"),
            actions=[{"deviceId": "alarm", "action": "arm"}],
        )
        rule_closed = sa.AutomationRule(
            rule_id="r-closed",
            condition=sa.Condition(sensor_id="d-eval",
                                    operator=sa.Operator.EQ,
                                    value="closed"),
            actions=[{"deviceId": "alarm", "action": "disarm"}],
        )
        engine.add_rule(rule_open)
        engine.add_rule(rule_closed)

        sensor.update("open")
        open_triggers = engine.evaluate(sensor, "open")
        open_ids = {getattr(r, "rule_id", None) for r in open_triggers or []}

        sensor.update("closed")
        closed_triggers = engine.evaluate(sensor, "closed")
        closed_ids = {getattr(r, "rule_id", None) for r in closed_triggers or []}

        passed = open_ids == {"r-open"} and closed_ids == {"r-closed"}
        print_result(name, "PASS" if passed else "FAIL",
                     {"open_ids": list(open_ids), "closed_ids": list(closed_ids)})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", {"exception": repr(exc)})
        return False


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main():
    print("Running sensors + automation tests...\n")
    if sa is None:
        print("NOTE: src.sensors_automation could not be imported. All tests will SKIP.\n")
        print(_import_trace)
    else:
        print(f"NOTE: using sensors_automation from {sa.__name__}\n")

    tests = [
        test_public_surface_exists,
        test_motion_sensor_validates_bool,
        test_temperature_sensor_respects_range,
        test_humidity_sensor_bounds,
        test_door_window_sensor_accepts_open_closed,
        test_create_sensor_factory_returns_correct_types,
        test_disconnected_sensor_drops_direct_readings,
        test_unknown_sensor_id_is_dropped_silently,
        test_ingest_reading_autoconnects_offline_sensor,
        test_bad_packet_does_not_permanently_mute_sensor,
        test_sensor_manager_listeners_receive_valid_readings,
        test_automation_rule_fires_on_match,
        test_disabled_rule_does_not_fire,
        test_engine_tolerates_broken_dispatcher,
        test_evaluate_returns_triggered_rules,
    ]

    passed = failed = skipped = 0
    for test in tests:
        try:
            result = test()
        except Exception as exc:
            print_result(test.__name__, "FAIL", {"exception": repr(exc)})
            failed += 1
            continue

        if result is None:
            skipped += 1
        elif result:
            passed += 1
        else:
            failed += 1

    total = len(tests)
    print(f"\nSummary: {passed} passed, {failed} failed, {skipped} skipped of {total}.")


if __name__ == "__main__":
    main()
