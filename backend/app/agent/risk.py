"""Risk and policy helpers for the AI Network Agent.

This module intentionally uses deterministic rules. The LLM may explain a
request, but backend policy decides whether an action is read-only, guarded,
approval-required, or blocked.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AgentPolicy(StrEnum):
    READ_ONLY = "READ_ONLY"
    GUARDED = "GUARDED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    BLOCKED = "BLOCKED"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class RiskAssessment:
    policy: AgentPolicy
    risk: RiskLevel
    reason: str
    approval_required: bool

    def to_dict(self) -> dict:
        return {
            "policy": self.policy.value,
            "risk": self.risk.value,
            "reason": self.reason,
            "approval_required": self.approval_required,
        }


READ_ONLY_PATTERNS = (
    "cek ",
    "check ",
    "show ",
    "display ",
    "tampilkan ",
    "lihat ",
    "status ",
    "monitor ",
    "ping ",
    "traceroute ",
    "trace ",
    "print ",
    "jelaskan",
    "explain",
    "rincian",
    "apa saja",
    "/ip address print",
    "/interface print",
    "/ip route print",
    "/routing",
    "journalctl",
    "systemctl status",
    "docker ps",
)

READ_ONLY_PREFIX_ONLY_PATTERNS = (
    "ss ",
    "ip addr",
    "ip route",
)

CHANGE_PATTERNS = (
    "configure",
    "konfigurasi",
    "config ",
    "set ",
    "buat vlan",
    "create vlan",
    "ip address ",
    "no shutdown",
    "shutdown",
    "deploy",
    "apply",
    "restore",
    "restart ",
    "systemctl restart",
    "install ",
    "delete ",
    "hapus ",
    "remove ",
    "add ",
    "enable ",
    "disable ",
    "tambah",
    "ubah",
    "ganti",
    "nonaktifkan",
    "aktifkan",
    "matikan",
    "nyalakan",
)

BLOCKED_PATTERNS = (
    "rm -rf /",
    "mkfs",
    "wipefs",
    "dd if=",
    "format disk",
    "write erase",
    "erase startup-config",
    "factory reset",
    "export password",
    "show running-config | include password",
)


def normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def assess_text_risk(message: str) -> RiskAssessment:
    normalized = normalize_text(message)
    if not normalized:
        return RiskAssessment(
            policy=AgentPolicy.GUARDED,
            risk=RiskLevel.LOW,
            reason="Empty or unclear request",
            approval_required=False,
        )

    if any(pattern in normalized for pattern in BLOCKED_PATTERNS):
        return RiskAssessment(
            policy=AgentPolicy.BLOCKED,
            risk=RiskLevel.CRITICAL,
            reason="Request matches blocked destructive or secret-exposure pattern",
            approval_required=False,
        )

    if (
        normalized.startswith(READ_ONLY_PATTERNS)
        or normalized.startswith(READ_ONLY_PREFIX_ONLY_PATTERNS)
        or any(pattern in normalized for pattern in READ_ONLY_PATTERNS)
    ):
        return RiskAssessment(
            policy=AgentPolicy.READ_ONLY,
            risk=RiskLevel.LOW,
            reason="Request is read-only inspection",
            approval_required=False,
        )

    if any(pattern in normalized for pattern in CHANGE_PATTERNS):
        return RiskAssessment(
            policy=AgentPolicy.APPROVAL_REQUIRED,
            risk=RiskLevel.MEDIUM,
            reason="Request can change device, lab, service, or workspace state",
            approval_required=True,
        )

    return RiskAssessment(
        policy=AgentPolicy.GUARDED,
        risk=RiskLevel.LOW,
        reason="Request needs guarded interpretation before execution",
        approval_required=False,
    )
