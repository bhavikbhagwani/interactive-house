"""Extended sensors and automation tests (types, conditions, engine, manager).

Run from ``server/``::

    python tests/test_sensors_automation/test_sensors_automation_extended.py
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
    _trace = traceback.format_exc()
else:
    _trace = ""


def print_result(name: str, status: str, details=None) -> None:
    print(f"[{status}] {name}")
    if details is not None:
        print("   Details:", details)


def test_condition_operators_n_eq_lt():
    name = "Condition NEQ, LT, GTE match readings"
    if sa is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        s = sa.TemperatureSensor("t-cond", name="T")
        s.mark_online()
        c_eq = sa.Condition("t-cond", sa.Operator.EQ, 20)
        c_neq = sa.Condition("t-cond", sa.Operator.NEQ, 20)
        c_lt = sa.Condition("t-cond", sa.Operator.LT, 25)
        c_gte = sa.Condition("t-cond", sa.Operator.GTE, 20)
        assert c_eq.matches(s, 20) and not c_eq.matches(s, 21)
        assert c_neq.matches(s, 21) and not c_neq.matches(s, 20)
        assert c_lt.matches(s, 20) and c_lt.matches(s, 10)
        assert c_gte.matches(s, 20) and c_gte.matches(s, 30)
        print_result(name, "PASS", None)
        return True
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_humidity_rule_fires_dehumidifier():
    name = "Humidity > 70 dispatches dehumidifier on"
    if sa is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        mgr = sa.SensorManager()
        eng = sa.AutomationEngine()
        eng.attach(mgr)
        out = []

        def d(device_id, action):
            out.append((device_id, action))

        eng.set_dispatcher(d)
        mgr.register_new(sa.SensorType.HUMIDITY, "h-1", name="Bath")
        eng.add_rule(
            sa.AutomationRule(
                "hum-high",
                sa.Condition("h-1", sa.Operator.GT, 70.0),
                [{"deviceId": "dehum-1", "action": "on"}],
            )
        )
        mgr.ingest_reading("h-1", 50)
        a = list(out)
        mgr.ingest_reading("h-1", 75)
        b = list(out)
        passed = len(a) == 0 and len(b) == 1 and b[0] == ("dehum-1", "on")
        print_result(name, "PASS" if passed else "FAIL", {"out": out})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_door_window_open_triggers():
    name = "DoorWindowSensor open string fires rule"
    if sa is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        mgr = sa.SensorManager()
        eng = sa.AutomationEngine()
        eng.attach(mgr)
        log = []
        eng.set_dispatcher(lambda d, a: log.append(f"{d}:{a}"))
        mgr.register_new(
            sa.SensorType.DOOR_WINDOW,
            "dw-1",
            name="Front",
        )
        eng.add_rule(
            sa.AutomationRule(
                "dw-open",
                sa.Condition("dw-1", sa.Operator.EQ, "open"),
                [{"deviceId": "chime-1", "action": "ring"}],
            )
        )
        mgr.ingest_reading("dw-1", "closed")
        n0 = len(log)
        mgr.ingest_reading("dw-1", "open")
        passed = n0 == 0 and log == ["chime-1:ring"]
        print_result(name, "PASS" if passed else "FAIL", {"log": log})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_two_rules_same_sensor_different_thresholds():
    name = "Two rules on same temp sensor: cold vs hot"
    if sa is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        mgr = sa.SensorManager()
        eng = sa.AutomationEngine()
        eng.attach(mgr)
        log = []
        eng.set_dispatcher(lambda d, a: log.append((d, a)))
        mgr.register_new(sa.SensorType.TEMPERATURE, "t2", name="T")
        eng.add_rule(
            sa.AutomationRule(
                "too-cold",
                sa.Condition("t2", sa.Operator.LT, 5.0),
                [{"deviceId": "heater-1", "action": "on"}],
            )
        )
        eng.add_rule(
            sa.AutomationRule(
                "too-hot",
                sa.Condition("t2", sa.Operator.GT, 30.0),
                [{"deviceId": "ac-1", "action": "on"}],
            )
        )
        mgr.ingest_reading("t2", 3)
        a = list(log)
        log.clear()
        mgr.ingest_reading("t2", 20)
        mid = list(log)
        log.clear()
        mgr.ingest_reading("t2", 35)
        hot = list(log)
        passed = a == [("heater-1", "on")] and mid == [] and hot == [("ac-1", "on")]
        print_result(
            name,
            "PASS" if passed else "FAIL",
            {"cold": a, "mid": mid, "hot": hot},
        )
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_motion_false_branch():
    name = "Motion EQ False dispatches (e.g. all clear)"
    if sa is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        mgr = sa.SensorManager()
        eng = sa.AutomationEngine()
        eng.attach(mgr)
        log = []
        eng.set_dispatcher(lambda d, a: log.append((d, a)))
        mgr.register_new(sa.SensorType.MOTION, "m-clear", name="M")
        eng.add_rule(
            sa.AutomationRule(
                "no-motion",
                sa.Condition("m-clear", sa.Operator.EQ, False),
                [{"deviceId": "lights-1", "action": "dim"}],
            )
        )
        mgr.ingest_reading("m-clear", True)
        t = list(log)
        log.clear()
        mgr.ingest_reading("m-clear", False)
        f = list(log)
        passed = t == [] and f == [("lights-1", "dim")]
        print_result(name, "PASS" if passed else "FAIL", {"true_read": t, "false_read": f})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_sensor_manager_unregister():
    name = "unregister removes sensor; ingest is ignored"
    if sa is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        mgr = sa.SensorManager()
        mgr.register_new(sa.SensorType.MOTION, "m-x", name="M")
        mgr.unregister("m-x")
        mgr.ingest_reading("m-x", True)  # should not crash
        print_result(name, "PASS", None)
        return True
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_list_sensors():
    name = "SensorManager list_sensors returns registered ids"
    if sa is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        mgr = sa.SensorManager()
        mgr.register_new(sa.SensorType.TEMPERATURE, "a", name="A")
        mgr.register_new(sa.SensorType.MOTION, "b", name="B")
        ids = {s.sensor_id for s in mgr.list_sensors()}
        passed = ids == {"a", "b"}
        print_result(name, "PASS" if passed else "FAIL", {"ids": ids})
        return passed
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def test_rule_to_dict_roundtrip_info():
    name = "AutomationRule.to_dict includes condition and actions"
    if sa is None:
        print_result(name, "SKIP", _trace)
        return None
    try:
        rule = sa.AutomationRule(
            "r1",
            sa.Condition("s1", sa.Operator.EQ, 1),
            [{"deviceId": "d1", "action": "x"}],
            name="R",
        )
        d = rule.to_dict()
        passed = d.get("ruleId") == "r1" and d.get("actions")  # type: ignore[union-attr]
        print_result(name, "PASS" if passed else "FAIL", d)
        return bool(passed)
    except Exception as exc:
        print_result(name, "FAIL", repr(exc))
        return False


def main():
    print("Running extended sensors and automation tests...\n")
    if sa is None:
        print(_trace)
        return
    tests = [
        test_condition_operators_n_eq_lt,
        test_humidity_rule_fires_dehumidifier,
        test_door_window_open_triggers,
        test_two_rules_same_sensor_different_thresholds,
        test_motion_false_branch,
        test_sensor_manager_unregister,
        test_list_sensors,
        test_rule_to_dict_roundtrip_info,
    ]
    passed = failed = skipped = 0
    for t in tests:
        try:
            r = t()
            if r is None:
                skipped += 1
            elif r:
                passed += 1
            else:
                failed += 1
        except Exception as exc:
            print_result(t.__name__, "FAIL", repr(exc))
            failed += 1
    n = len(tests)
    print(f"\nSummary: {passed} passed, {failed} failed, {skipped} skipped of {n}.")


if __name__ == "__main__":
    main()
