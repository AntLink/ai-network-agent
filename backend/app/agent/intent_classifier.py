"""Deterministic intent classifier for the AI Network Agent."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.agent.risk import AgentPolicy, RiskAssessment, assess_text_risk


class IntentType(StrEnum):
    HOW_TO_USE = "how_to_use"
    SOFTWARE_TASK = "software_task"
    LINUX_ADMIN = "linux_admin"
    NETWORK_READONLY = "network_readonly"
    NETWORK_CHANGE = "network_change"
    DEVICE_INVENTORY = "device_inventory"
    GNS3_TOPOLOGY_GENERATE = "gns3_topology_generate"
    LAB_MANAGEMENT = "lab_management"
    TROUBLESHOOTING = "troubleshooting"
    CLARIFICATION = "clarification"


@dataclass(frozen=True)
class IntentTarget:
    kind: str
    id: str = ""
    name: str = ""
    vendor: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "id": self.id,
            "name": self.name,
            "vendor": self.vendor,
        }


@dataclass(frozen=True)
class AgentIntent:
    type: IntentType
    targets: tuple[IntentTarget, ...] = ()
    policy: AgentPolicy = AgentPolicy.GUARDED
    confidence: float = 0.5
    reason: str = ""
    risk: str = "low"
    ambiguous: bool = False
    missing_context: str = ""
    suggested_tools: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "targets": [target.to_dict() for target in self.targets],
            "policy": self.policy.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "risk": self.risk,
            "ambiguous": self.ambiguous,
            "missing_context": self.missing_context,
            "suggested_tools": list(self.suggested_tools),
        }


def classify_intent(
    message: str,
    *,
    inventory: list[dict[str, Any]] | None = None,
    device_ids: list[str] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> AgentIntent:
    text = _normalize(message)
    risk = assess_text_risk(message)
    targets, ambiguous_reason = _resolve_targets(text, inventory or [], device_ids or [])
    intent_type = _classify_type(text, risk)
    suggested_tools = _suggest_tools(intent_type, targets, text)

    if ambiguous_reason:
        return AgentIntent(
            type=IntentType.CLARIFICATION,
            targets=tuple(targets),
            policy=AgentPolicy.GUARDED,
            confidence=0.76,
            reason=ambiguous_reason,
            risk=risk.risk.value,
            ambiguous=True,
            missing_context=ambiguous_reason,
            suggested_tools=(),
        )

    if _is_short_follow_up(text) and not targets and history:
        history_targets = _targets_from_history(history, inventory or [])
        if history_targets:
            targets = history_targets
            suggested_tools = _suggest_tools(intent_type, targets, text)

    confidence = 0.86 if targets or intent_type in {IntentType.HOW_TO_USE, IntentType.SOFTWARE_TASK} else 0.68
    return AgentIntent(
        type=intent_type,
        targets=tuple(targets),
        policy=risk.policy,
        confidence=confidence,
        reason=risk.reason,
        risk=risk.risk.value,
        ambiguous=False,
        suggested_tools=tuple(suggested_tools),
    )


def _classify_type(text: str, risk: RiskAssessment) -> IntentType:
    if any(token in text for token in ("cara pakai", "cara menggunakan", "gimana menggunakan", "tutorial", "panduan")):
        return IntentType.HOW_TO_USE
    if any(token in text for token in ("buat fitur", "ubah kode", "fix bug", "jalankan test", "build error", "lint", "buat tools", "buat tool", "buat program", "buat script", "buat skrip", "tulis program", "tulis script", "tulis kode", "buat kode", "fix error", "debug", "compile error", "buat aplikasi", "analisa kode", "analisis kode", "pahami kode", "periksa kode", "perbaiki kode", "perbaiki bug", "cari bug", "jalankan program", "jalankan script", "jalankan kode", "jalanin program", "run code", "menjalankan program", "sample code", "contoh kode", "buat cli", "buat api")):
        return IntentType.SOFTWARE_TASK
    if any(token in text for token in ("frigate", "systemctl", "journalctl", "docker", "ubuntu", "linux", "nginx", "service ")):
        return IntentType.LINUX_ADMIN
    if any(token in text for token in ("topologi", "topology", "generate lab", "buatkan lab", "gns3 template")):
        return IntentType.GNS3_TOPOLOGY_GENERATE
    if any(token in text for token in ("start lab", "stop lab", "restart lab", "project gns3", "containerlab", "vrnetlab")):
        return IntentType.LAB_MANAGEMENT
    if any(token in text for token in ("tambah device", "edit device", "hapus device", "list device", "inventory")):
        return IntentType.DEVICE_INVENTORY
    if risk.policy == AgentPolicy.APPROVAL_REQUIRED:
        return IntentType.NETWORK_CHANGE
    if any(token in text for token in ("kenapa", "troubleshoot", "tidak bisa", "gagal", "down", "error", "loss")):
        return IntentType.TROUBLESHOOTING
    return IntentType.NETWORK_READONLY


def _resolve_targets(
    text: str,
    inventory: list[dict[str, Any]],
    explicit_device_ids: list[str],
) -> tuple[list[IntentTarget], str]:
    lookup: dict[str, dict[str, Any]] = {}
    for device in inventory:
        device_id = str(device.get("id", "")).lower()
        hostname = str(device.get("hostname", "")).lower()
        if device_id:
            lookup[device_id] = device
        if hostname:
            lookup[hostname] = device

    targets: list[IntentTarget] = []
    seen: set[str] = set()
    for device_id in explicit_device_ids:
        device = next((item for item in inventory if str(item.get("id")) == str(device_id)), None)
        if device:
            _append_device_target(targets, seen, device)

    words = set(re.findall(r"[a-z0-9][a-z0-9_.-]*", text))
    for word in words:
        exact = lookup.get(word)
        if exact:
            _append_device_target(targets, seen, exact)
            continue
        # Suffix match: a short token like "mt1" can be the trailing segment of
        # a device id/hostname ("static-routing-mt1", "SR-MT1").
        if len(word) >= 3:
            suffix_matches = []
            for device in inventory:
                candidates = (
                    str(device.get("id", "")).lower(),
                    str(device.get("hostname", "")).lower(),
                )
                if any(
                    candidate and candidate != word and candidate.endswith(word)
                    for candidate in candidates
                ):
                    suffix_matches.append(device)
            if len(suffix_matches) == 1:
                _append_device_target(targets, seen, suffix_matches[0])

    ambiguous_tokens = []
    for word in words:
        if not word or word in lookup:
            continue
        matches = []
        for device in inventory:
            candidates = (
                str(device.get("id", "")).lower(),
                str(device.get("hostname", "")).lower(),
            )
            if any(candidate.startswith(word) for candidate in candidates if candidate):
                if device not in matches:
                    matches.append(device)
            elif len(word) >= 3 and any(
                candidate and candidate != word and candidate.endswith(word)
                for candidate in candidates
            ):
                if device not in matches:
                    matches.append(device)
        if len(matches) > 1:
            ambiguous_tokens.append(f"{word}: {', '.join(str(item.get('hostname') or item.get('id')) for item in matches[:5])}")
        elif len(word) <= 3 and len(matches) >= 1:
            ambiguous_tokens.append(f"{word}: {', '.join(str(item.get('hostname') or item.get('id')) for item in matches[:5])}")

    if ambiguous_tokens and not targets:
        return targets, "Target device ambigu: " + "; ".join(ambiguous_tokens)

    fuzzy_hints = []
    if not targets:
        candidates: list[tuple[str, dict[str, Any]]] = []
        for device in inventory:
            for candidate in (str(device.get("id", "")).lower(), str(device.get("hostname", "")).lower()):
                if candidate:
                    candidates.append((candidate, device))
        for word in words:
            if not word or len(word) < 4 or word in lookup:
                continue
            best: tuple[str, dict[str, Any]] | None = None
            best_dist = 99
            for candidate, device in candidates:
                distance = _levenshtein(word, candidate)
                if distance < best_dist:
                    best_dist = distance
                    best = (candidate, device)
            if best is not None and 0 < best_dist <= 2:
                fuzzy_hints.append(
                    f"'{word}' mungkin maksudnya '{best[0]}' "
                    f"({str(best[1].get('hostname') or best[1].get('id'))})?"
                )

    if fuzzy_hints:
        return targets, "Device tidak dikenal. " + "; ".join(fuzzy_hints[:3])

    return targets, ""


def _levenshtein(a: str, b: str) -> int:
    """Compute the Levenshtein edit distance between two strings."""
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            insert = current[j - 1] + 1
            delete = prev[j] + 1
            substitute = prev[j - 1] + (0 if char_a == char_b else 1)
            current.append(min(insert, delete, substitute))
        prev = current
    return prev[-1]


def _append_device_target(targets: list[IntentTarget], seen: set[str], device: dict[str, Any]) -> None:
    device_id = str(device.get("id", ""))
    if not device_id or device_id in seen:
        return
    seen.add(device_id)
    targets.append(
        IntentTarget(
            kind="device",
            id=device_id,
            name=str(device.get("hostname") or device_id),
            vendor=str(device.get("vendor") or "other").lower(),
        )
    )


def _targets_from_history(history: list[dict[str, Any]], inventory: list[dict[str, Any]]) -> list[IntentTarget]:
    for item in reversed(history[-8:]):
        content = _normalize(str(item.get("content") or item.get("text") or ""))
        targets, _ = _resolve_targets(content, inventory, [])
        if targets:
            return targets
    return []


def _suggest_tools(intent_type: IntentType, targets: list[IntentTarget], text: str) -> list[str]:
    tools: list[str] = []
    vendors = {target.vendor for target in targets}
    if intent_type in {IntentType.NETWORK_READONLY, IntentType.TROUBLESHOOTING}:
        if "interface" in text or "ip address" in text:
            tools.append("devices.interfaces")
        if "route" in text or "routing" in text:
            tools.append("devices.routes")
        if "config" in text or "konfigurasi" in text or "configuration" in text or "startup" in text:
            tools.append("devices.config")
        if "status" in text or not tools:
            tools.append("devices.health")
    if intent_type == IntentType.LINUX_ADMIN:
        tools.extend(["linux.service_status", "linux.exec_readonly"])
    if intent_type == IntentType.SOFTWARE_TASK:
        tools.extend(["workspace.search_code", "workspace.read_file", "workspace.write_file", "workspace.edit_file", "workspace.run_command", "workspace.run_tests", "workspace.run_lint", "workspace.run_build"])
    if intent_type == IntentType.NETWORK_CHANGE:
        tools.extend(["devices.config", "devices.backup_config", "devices.deploy_config", "devices.verify_change"])
    if intent_type == IntentType.GNS3_TOPOLOGY_GENERATE:
        tools.extend(["gns3.templates.list", "topology.generate_from_intent", "topology.save_snapshot"])
    if "cisco" in vendors:
        tools.append("cisco.exec_readonly")
    if "mikrotik" in vendors:
        tools.append("mikrotik.exec_readonly")
    if "aruba" in vendors:
        tools.append("aruba.exec_readonly")
    return list(dict.fromkeys(tools))


def _is_short_follow_up(text: str) -> bool:
    return text in {"ok", "oke", "lanjut", "lanjutkan", "terus", "teruskan", "iya", "ya", "gas"}


def _normalize(value: str) -> str:
    return " ".join((value or "").strip().lower().split())
