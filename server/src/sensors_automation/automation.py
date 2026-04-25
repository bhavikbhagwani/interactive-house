"""
Automation engine.

A :class:`AutomationRule` binds a :class:`Condition` (evaluated against a
sensor reading) to one or more :class:`DeviceAction`-style payloads. The
:class:`AutomationEngine` subscribes to a :class:`SensorManager` and fires
the configured device actions whenever a rule's condition becomes true.

The engine is transport-agnostic: callers pass in an ``action_dispatcher``
callable ``dispatch(device_id, action)`` that is responsible for the
actual device message (the existing server can wire this to its own
``handle_action`` / ``safe_send_json``).
"""

from typing import Any, Callable, Dict, List, Optional

from .sensors import Sensor


# =========================================================
# CONDITIONS
# =========================================================


class Operator:
    EQ = "=="
    NEQ = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="

    ALL = (EQ, NEQ, GT, GTE, LT, LTE)


class Condition:
    """Compare a sensor reading to a threshold value."""

    def __init__(self, sensor_id: str, operator: str, value: Any):
        if operator not in Operator.ALL:
            raise ValueError(f"Unsupported operator: {operator!r}")
        self.sensor_id = sensor_id
        self.operator = operator
        self.value = value

    def matches(self, sensor: Sensor, reading: Any) -> bool:
        if sensor.sensor_id != self.sensor_id:
            return False
        return _compare(reading, self.operator, self.value)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensorId": self.sensor_id,
            "operator": self.operator,
            "value": self.value,
        }


def _compare(left: Any, operator: str, right: Any) -> bool:
    try:
        if operator == Operator.EQ:
            return left == right
        if operator == Operator.NEQ:
            return left != right
        if operator == Operator.GT:
            return left > right
        if operator == Operator.GTE:
            return left >= right
        if operator == Operator.LT:
            return left < right
        if operator == Operator.LTE:
            return left <= right
    except TypeError:
        # e.g. comparing bool/string with number. Treat as no match rather
        # than raising -- automation should never crash the server.
        return False
    return False


# =========================================================
# RULES
# =========================================================


class AutomationRule:
    """A named rule: when ``condition`` holds, dispatch ``actions``."""

    def __init__(
        self,
        rule_id: str,
        condition: Condition,
        actions: List[Dict[str, Any]],
        name: Optional[str] = None,
        enabled: bool = True,
    ):
        if not rule_id:
            raise ValueError("rule_id is required")
        if not isinstance(condition, Condition):
            raise TypeError("condition must be a Condition instance")
        if not actions:
            raise ValueError("rule must define at least one action")
        for action in actions:
            if not isinstance(action, dict):
                raise TypeError("each action must be a dict")
            if "deviceId" not in action or "action" not in action:
                raise ValueError(
                    "each action must include 'deviceId' and 'action'"
                )
        self.rule_id = rule_id
        self.name = name or rule_id
        self.condition = condition
        self.actions = list(actions)
        self.enabled = bool(enabled)
        self.last_triggered: Optional[str] = None
        self.trigger_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ruleId": self.rule_id,
            "name": self.name,
            "enabled": self.enabled,
            "condition": self.condition.to_dict(),
            "actions": list(self.actions),
            "lastTriggered": self.last_triggered,
            "triggerCount": self.trigger_count,
        }


# =========================================================
# ENGINE
# =========================================================


class AutomationEngine:
    """Evaluates :class:`AutomationRule` s on every sensor reading."""

    def __init__(
        self,
        sensor_manager=None,
        action_dispatcher: Optional[Callable[[str, str], Any]] = None,
    ):
        self._rules: Dict[str, AutomationRule] = {}
        self._dispatcher = action_dispatcher
        self._sensor_manager = None
        if sensor_manager is not None:
            self.attach(sensor_manager)

    # -- wiring --------------------------------------------------------

    def attach(self, sensor_manager):
        self._sensor_manager = sensor_manager
        sensor_manager.add_listener(self._on_reading)

    def detach(self):
        if self._sensor_manager is not None:
            self._sensor_manager.remove_listener(self._on_reading)
            self._sensor_manager = None

    def set_dispatcher(self, dispatcher: Callable[[str, str], Any]):
        self._dispatcher = dispatcher

    # -- rule CRUD -----------------------------------------------------

    def add_rule(self, rule: AutomationRule) -> AutomationRule:
        if rule.rule_id in self._rules:
            raise ValueError(f"Rule {rule.rule_id} already exists")
        self._rules[rule.rule_id] = rule
        return rule

    def remove_rule(self, rule_id: str) -> Optional[AutomationRule]:
        return self._rules.pop(rule_id, None)

    def get_rule(self, rule_id: str) -> Optional[AutomationRule]:
        return self._rules.get(rule_id)

    def list_rules(self) -> List[AutomationRule]:
        return list(self._rules.values())

    def set_rule_enabled(self, rule_id: str, enabled: bool):
        rule = self._rules.get(rule_id)
        if rule is None:
            raise KeyError(f"Unknown rule: {rule_id}")
        rule.enabled = bool(enabled)

    # -- evaluation ----------------------------------------------------

    def evaluate(self, sensor: Sensor, reading: Any) -> List[AutomationRule]:
        """Return the list of rules that fired for this reading."""
        triggered: List[AutomationRule] = []
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            if rule.condition.sensor_id != sensor.sensor_id:
                continue
            if not rule.condition.matches(sensor, reading):
                continue
            self._fire(rule)
            triggered.append(rule)
        return triggered

    def _on_reading(self, sensor: Sensor, reading: Any):
        self.evaluate(sensor, reading)

    def _fire(self, rule: AutomationRule):
        from datetime import datetime, timezone

        rule.last_triggered = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )
        rule.trigger_count += 1

        if self._dispatcher is None:
            return

        for action in rule.actions:
            try:
                self._dispatcher(action["deviceId"], action["action"])
            except Exception:  # pragma: no cover - defensive
                # Never let a broken downstream take out automation.
                pass
