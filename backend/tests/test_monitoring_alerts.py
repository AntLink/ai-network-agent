"""Milestone 4: rule-based monitoring alert evaluation."""
from datetime import datetime, timezone

import pytest

from app.services.monitoring_alerts import AlertRule, evaluate_metrics


def test_high_cpu_triggers_critical_alert():
    alerts = evaluate_metrics({"cpu": 95, "memory": 50}, device_id="r1")
    sev = {a["severity"] for a in alerts}
    assert "critical" in sev
    assert all(a["device_id"] == "r1" for a in alerts)


def test_normal_metrics_produce_no_alerts():
    alerts = evaluate_metrics({"cpu": 40, "memory": 50}, device_id="r1")
    assert alerts == []


def test_multidimensional_cpu_and_memory():
    alerts = evaluate_metrics({"cpu": 95, "memory": 95}, device_id="r1")
    metrics = {a["metric"] for a in alerts}
    assert {"cpu", "memory"}.issubset(metrics)
    # both metrics have a critical (>90) alert
    critical_metrics = {a["metric"] for a in alerts if a["severity"] == "critical"}
    assert {"cpu", "memory"}.issubset(critical_metrics)


def test_per_device_rule_scoping():
    rule = AlertRule("cpu", "gt", 50, "warn", "r1 cpu high", device_id="r1")
    # device matches -> alert
    got = evaluate_metrics({"cpu": 60}, device_id="r1", rules=[rule])
    assert len(got) == 1 and got[0]["device_id"] == "r1"
    # shared "*" rule applies to any device
    shared = AlertRule("cpu", "gt", 50, "warn", "cpu high")
    got2 = evaluate_metrics({"cpu": 60}, device_id="other", rules=[shared])
    assert len(got2) == 1


def test_operator_lte_and_lt():
    rules = [
        AlertRule("cpu", "lte", 10, "info", "cpu very low"),
        AlertRule("cpu", "lt", 20, "info", "cpu below 20"),
    ]
    got = evaluate_metrics({"cpu": 5}, device_id="r1", rules=rules)
    assert len(got) == 2


def test_unresolvable_metric_ignored():
    alerts = evaluate_metrics({"cpu": 90, "unknown": None}, device_id="r1")
    assert all(a["metric"] == "cpu" for a in alerts)


def test_invalid_severity_filtered():
    rule = AlertRule("cpu", "gt", 50, "bogus", "x")
    alerts = evaluate_metrics({"cpu": 60}, device_id="r1", rules=[rule])
    assert alerts == []


def test_alert_is_deterministic_and_has_expected_fields():
    now = datetime(2026, 9, 4, tzinfo=timezone.utc)
    alerts = evaluate_metrics({"cpu": 99}, device_id="r1", now=now)
    a = alerts[0]
    assert a["status"] == "open"
    assert a["severity"] == "critical"
    assert a["value"] == 99.0
    assert a["threshold"] == 90.0
    assert a["type"] == "monitoring"
