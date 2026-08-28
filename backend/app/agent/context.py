"""Device/session context resolver for the AI Network Agent.

Extracted from the monolithic `agent.py` so the chat endpoints and any future
orchestrator share one deterministic resolver for:

- inventory lookup,
- device detection from a user message,
- ambiguous-device detection,
- multi-device request detection,
- session/history device focus resolution,
- short follow-up detection.
"""
from __future__ import annotations

import re
from typing import Any


def get_inventory() -> list[dict[str, Any]]:
    try:
        from app.repositories.inventory import inventory_repository
        return inventory_repository.list_devices()
    except Exception:
        return []


def find_devices(message: str, device_id: str = "") -> list[str]:
    """Match device names/ids mentioned in the message against inventory."""
    devices: list[str] = []
    inventory = get_inventory()

    if device_id:
        devices.append(device_id)

    msg_lower = message.lower()
    normalized_tokens = {
        token.strip().lower()
        for token in re.findall(r"[a-z0-9][a-z0-9._-]*", msg_lower)
        if token.strip()
    }

    # 1. Specific device match (id / hostname / first word token).
    for device in inventory:
        dev_id = str(device.get("id", ""))
        hostname = str(device.get("hostname", ""))
        first_word = hostname.split()[0] if hostname.split() else ""

        for token in (dev_id, hostname, first_word):
            normalized = token.strip().lower()
            if normalized and normalized in normalized_tokens and dev_id not in devices:
                devices.append(dev_id)
                break

    # 2. Suffix matching: a short token like "mt1" can be the trailing segment
    #    of a device id/hostname ("static-routing-mt1", "SR-MT1"). Resolve only
    #    when the token maps to exactly one device to avoid ambiguity.
    if not devices:
        for token in sorted(normalized_tokens, key=len, reverse=True):
            if len(token) < 3:
                continue
            suffix_matches: list[str] = []
            for device in inventory:
                dev_id = str(device.get("id", "")).lower()
                hostname = str(device.get("hostname", "")).lower()
                id_match = dev_id and dev_id != token and dev_id.endswith(token)
                hostname_match = hostname and hostname != token and hostname.endswith(token)
                if id_match or hostname_match:
                    real_id = str(device.get("id", "")).strip()
                    if real_id and real_id not in suffix_matches:
                        suffix_matches.append(real_id)
            if len(suffix_matches) == 1:
                devices.append(suffix_matches[0])
                break

    # 3. Vendor fallback: only when no specific device was identified.
    if not devices:
        for device in inventory:
            vendor = str(device.get("vendor", "")).strip().lower()
            dev_id = str(device.get("id", "")).strip()
            if vendor and dev_id and vendor in normalized_tokens and dev_id not in devices:
                devices.append(dev_id)

    return devices


def find_devices_from_message(message: str) -> list[str]:
    """Find devices mentioned explicitly in the current user message only."""
    return find_devices(message, "")


def has_ambiguous_device_reference(message: str) -> bool:
    """Detect device-like tokens that are too short to resolve safely."""
    msg_lower = message.lower()
    tokens = {
        token.strip().lower()
        for token in re.findall(r"[a-z0-9][a-z0-9._-]*", msg_lower)
        if token.strip()
    }
    if not tokens:
        return False

    inventory = get_inventory()
    candidates: set[str] = set()
    for device in inventory:
        dev_id = str(device.get("id", "")).strip().lower()
        hostname = str(device.get("hostname", "")).strip().lower()
        first_word = hostname.split()[0] if hostname else ""
        for item in (dev_id, hostname, first_word):
            if item:
                candidates.add(item)

    for token in tokens:
        if len(token) <= 2 and any(candidate.startswith(token) and candidate != token for candidate in candidates):
            return True
        if len(token) <= 3 and any(candidate.startswith(token) and candidate != token for candidate in candidates):
            return True

    return False


def is_multi_device_request(message: str, device_ids: list[str] | None = None) -> bool:
    """Heuristically detect that the user expects more than one device."""
    if device_ids and len([item for item in device_ids if item]) >= 2:
        return True

    msg_lower = message.lower()
    conjunctions = (" dan ", " and ", ",", " sampai ", " serta ", " plus ")
    inventory_matches = find_devices(message)
    if len(inventory_matches) >= 2:
        return True
    return any(token in msg_lower for token in conjunctions) and bool(inventory_matches)


def history_device_ids(history: list[dict[str, Any]] | None) -> list[str]:
    """Infer device ids from the recent conversation transcript."""
    if not history:
        return []

    inventory = get_inventory()
    inferred: list[str] = []
    for item in history[-12:]:
        text = str(item.get("text", item.get("content", ""))).strip().lower()
        if not text:
            continue
        message_tokens = {
            token.strip().lower()
            for token in re.findall(r"[a-z0-9][a-z0-9._-]*", text)
            if token.strip()
        }
        for device in inventory:
            dev_id = str(device.get("id", "")).strip()
            hostname = str(device.get("hostname", "")).strip().lower()
            vendor = str(device.get("vendor", "")).strip().lower()
            platform = str(device.get("platform", "")).strip().lower()
            if not dev_id:
                continue
            device_tokens = [dev_id.lower(), hostname, vendor, platform]
            if any(token and token in message_tokens for token in device_tokens):
                if dev_id not in inferred:
                    inferred.append(dev_id)
    return inferred


def is_context_follow_up(message: str) -> bool:
    normalized = " ".join(message.strip().lower().replace("?", " ").replace("!", " ").split())
    if not normalized:
        return False

    short_cues = {
        "oke",
        "ok",
        "ya",
        "yes",
        "lanjut",
        "lanjutkan",
        "teruskan",
        "terus",
        "silakan",
        "detail",
        "jelaskan",
    }
    correction_cues = (
        "maksudnya",
        "bukannya",
        "bukan nya",
        "bukannya ada",
        "seharusnya",
        "harusnya",
        "kok",
        "kenapa",
        "padahal",
        "tapi",
        "namun",
        "masih sama",
        "masih belum",
        "belum muncul",
        "ada kan",
    )
    phrase_cues = (
        "yang tadi",
        "lanjut yang tadi",
        "cek itu",
        "lihat itu",
        "lanjutkan itu",
        "lebih detail",
        "bagaimana dengan itu",
        "apa langkah berikutnya",
        "apa yang harus saya lakukan",
    )
    return (
        normalized in short_cues
        or any(phrase in normalized for phrase in phrase_cues)
        or any(phrase in normalized for phrase in correction_cues)
    )


def resolve_session_context(
    *,
    session_id: str | None,
    device_ids: list[str] | None,
    lab_id: str | None,
    history: list[dict[str, Any]] | None,
    message: str,
    device_id: str = "",
) -> tuple[list[str], str]:
    """Keep the previous session focus when the current message is a short follow-up."""
    def _merge_device_ids(*groups: list[str] | None) -> list[str]:
        merged: list[str] = []
        for group in groups:
            for item in group or []:
                item = str(item).strip()
                if item and item not in merged:
                    merged.append(item)
        return merged

    current_device_ids = [item for item in (device_ids or []) if item]
    current_lab_id = str(lab_id or "")
    detected_device_ids = find_devices_from_message(message)
    multi_device_request = is_multi_device_request(message, detected_device_ids)
    ambiguous_device_reference = not detected_device_ids and has_ambiguous_device_reference(message)

    session_device_ids: list[str] = []
    session_lab_id = ""
    if session_id:
        try:
            from app.api.v1.endpoints.agent_sessions import get_session_context
            session_context = get_session_context(session_id) or {}
            session_device_ids = [item for item in session_context.get("device_ids", []) if item]
            session_lab_id = str(session_context.get("lab_id") or "")
        except Exception:
            session_device_ids = []
            session_lab_id = ""

    history_ids = history_device_ids(history)
    if detected_device_ids and not multi_device_request:
        inferred_device_ids = _merge_device_ids(detected_device_ids)
    elif ambiguous_device_reference:
        inferred_device_ids = []
    else:
        inferred_device_ids = _merge_device_ids(
            current_device_ids,
            detected_device_ids,
            session_device_ids,
            history_ids,
        )

    if is_context_follow_up(message) and not inferred_device_ids and not ambiguous_device_reference:
        inferred_device_ids = _merge_device_ids(session_device_ids, history_ids, ([device_id] if device_id else []))

    if multi_device_request:
        inferred_device_ids = _merge_device_ids(detected_device_ids, current_device_ids, session_device_ids, history_ids)

    resolved_lab_id = current_lab_id or session_lab_id
    return inferred_device_ids, resolved_lab_id
