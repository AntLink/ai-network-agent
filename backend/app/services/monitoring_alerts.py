"""Rule-based monitoring alert evaluation (Milestone 4).

Turns multidimensional device metrics (CPU, memory, ...) into structured alerts
using deterministic, declarative rules. Rules are evaluated by numeric thresholds
per severity; devices can opt into a shared rule set or receive device-specific
rules. Pure logic with no I/O so it is unit-testable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal

Operator = Literal["gt", "gte", "lt", "lte"]


@dataclass(frozen=True)
class AlertRule:
    metric: str
    operator: Operator
    threshold: float
    severity: str
    message: str
    device_id: str = "*"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Default cross-cutting rules. Per-device rules can be supplied by callers.
DEFAULT_RULES: list[AlertRule] = [
    AlertRule("cpu", "gt", 90, "critical", "CPU utilization above 90%"),
    AlertRule("cpu", "gt", 75, "warn", "CPU utilization above 75%"),
    AlertRule("memory", "gt", 90, "critical", "Memory utilization above 90%"),
    AlertRule("memory", "gt", 80, "warn", "Memory utilization above 80%"),
]


def _resolve(metrics: dict[str, Any], metric: str) -> float | None:
    """Resolve a metric value from a nested or flat metrics map (0-100 percent)."""
    if metric not in metrics:
        return None
    raw = metrics[metric]
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, dict):
        for key in ("usage", "percent", "value", "utilization"):
            if key in raw and isinstance(raw[key], (int, float)):
                return float(raw[key])
    return None


def _compare(value: float, op: Operator, threshold: float) -> bool:
    if op == "gt":
        return value > threshold
    if op == "gte":
        return value >= threshold
    if op == "lt":
        return value < threshold
    if op == "lte":
        return value <= threshold
    return False


def evaluate_metrics(
    metrics: dict[str, Any],
    *,
    rules: list[AlertRule] | None = None,
    device_id: str = "*",
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Evaluate metrics against rules and return triggered alerts.

    Returns a list of alert dicts (id, device_id, severity, metric, value,
    message, created_at, status=open). Only rules with a resolvable metric value
    and a matching device scope are evaluated.
    """
    rules = rules if rules is not None else DEFAULT_RULES
    now = now or datetime.now(timezone.utc)
    alerts: list[dict[str, Any]] = []
    for rule in rules:
        if rule.severity not in {"info", "warn", "critical"}:
            continue
        if rule.device_id not in {"*", device_id}:
            continue
        value = _resolve(metrics, rule.metric)
        if value is None:
            continue
        if _compare(value, rule.operator, rule.threshold):
            alert_id = (
                f"alert-{device_id}-{rule.metric}-{rule.operator}-"
                f"{int(rule.threshold)}-{now.strftime('%Y%m%d%H%M%S')}"
            )
            alerts.append(
                {
                    "id": alert_id,
                    "device_id": device_id,
                    "type": "monitoring",
                    "severity": rule.severity,
                    "metric": rule.metric,
                    "value": value,
                    "threshold": rule.threshold,
                    "message": rule.message,
                    "created_at": now.isoformat(),
                    "status": "open",
                }
            )
    return alerts
