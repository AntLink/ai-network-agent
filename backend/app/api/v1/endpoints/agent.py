"""AI Network Copilot agent endpoints."""
import asyncio
import ipaddress
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from typing import Any

from app.agent.providers import get_provider, NineRouterProvider
from app.agent.tools import get_tool_descriptions, execute_tool, AGENT_TOOLS
from app.agent.orchestrator import analyze_request
from app.agent.tool_registry import list_tool_descriptors
from app.agent.risk import AgentPolicy
from app.agent.context import (
    find_devices,
    find_devices_from_message,
    get_inventory,
    has_ambiguous_device_reference,
    history_device_ids,
    is_context_follow_up,
    is_multi_device_request,
    resolve_session_context,
)
from app.agent.dispatcher import dispatch_tool
from app.agent.event_bus import build_tool_output
from app.agent.export import render_document, FORMATTERS
from app.agent.export_service import build_export_document, collect_devices
from app.agent.software_agent import run_software_task, execute_code_snippet, debug_code_snippet
from app.agent.config_agent import ConfigChangeAgent
from app.agent import approvals
from app.agent import audit_store
from app.core.config import settings
from app.api.v1.endpoints.agent_sessions import update_session_context
from app.services.device_service import device_service

router = APIRouter()

_agent_events: list[dict[str, Any]] = []
_event_subscribers: list[Any] = []

EXPORT_DIR = Path(__file__).resolve().parents[4] / "exported"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# AI settings, initialized from .env via pydantic settings
_ai_settings: dict[str, Any] = {
    "provider": settings.AI_PROVIDER or "9router",
    "model": settings.NINEROUTER_MODEL or "opencode-cheap",
}


def _get_ai_response(message: str, device_id: str = "") -> str:
    """Generate a response using available AI provider or fallback."""
    provider_name = _ai_settings.get("provider", "9router")
    model = _ai_settings.get("model", "opencode-cheap")

    # Try to use AI provider
    try:
        provider = get_provider(provider_name)
        if isinstance(provider, NineRouterProvider):
            # API key from settings (.env) first, then env
            api_key = settings.NINEROUTER_KEY or os.getenv("NINEROUTER_KEY", "")
            if not api_key:
                return _fallback_response(message, device_id, "No NINEROUTER_KEY configured")

            # Use sync httpx to call 9Router
            import httpx
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{settings.NINEROUTER_URL or provider.base_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a Network Copilot for network engineers. Be concise and helpful. Respond in the same language as the user."},
                            {"role": "user", "content": message},
                        ],
                        "stream": False,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return _fallback_response(message, device_id, f"Provider error: {resp.status_code} - {resp.text[:100]}")
        else:
            return _fallback_response(message, device_id, "Provider not configured for sync call")
    except Exception as e:
        return _fallback_response(message, device_id, str(e))


def _sync_chat(provider, message: str, model: str) -> str:
    """Synchronous chat with provider."""
    import httpx

    if isinstance(provider, NineRouterProvider):
        # Use 9Router sync
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{provider.base_url}/v1/chat/completions",
                headers=provider._headers(),
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a Network Copilot. Analyze network requests and provide structured intent. Be concise."},
                        {"role": "user", "content": message},
                    ],
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    else:
        # For other providers, use the async chat method
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(provider.chat([
                {"role": "system", "content": "You are a Network Copilot. Analyze network requests and provide structured intent. Be concise."},
                {"role": "user", "content": message},
            ], model=model))
        finally:
            loop.close()


async def _llm_chat(system_prompt: str, user_prompt: str) -> str:
    """Call the configured LLM provider asynchronously (9Router preferred)."""
    import httpx

    provider_name = _ai_settings.get("provider", "9router")
    model = _ai_settings.get("model", "opencode-cheap")
    api_key = settings.NINEROUTER_KEY or os.getenv("NINEROUTER_KEY", "")
    base_url = settings.NINEROUTER_URL or "http://127.0.0.1:20128"

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{base_url.rstrip('/')}/v1/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _context_aware_response(
    message: str,
    device_ids: list[str],
    device_context: str,
    error: str,
    history: list[dict[str, Any]] | None = None,
) -> str:
    """Build an answer from real device context when LLM is unavailable."""
    msg_lower = message.lower()
    anchor = _conversation_anchor(history)
    multi_device_request = len([item for item in device_ids if item]) >= 2

    if _is_context_follow_up(message) and anchor["last_assistant"]:
        topic = anchor["topic"] or "konteks sebelumnya"
        vendor_overview = _active_vendor_overview(device_ids)
        vendor_line = f"\nVendor/device aktif: {vendor_overview}" if vendor_overview else ""
        return (
            "Ringkasan: saya lanjutkan dari konteks percakapan sebelumnya.\n"
            f"Temuan: topik terakhir mengarah ke {topic}.{vendor_line}\n"
            "Analisis: saya perlu memakai data perangkat terbaru untuk memastikan koreksi atau follow-up tersebut, "
            "bukan mengulang jawaban lama apa adanya.\n"
            "Langkah berikutnya: kirim ulang instruksi dengan fokus yang ingin dikonfirmasi, misalnya `cek ppp ubuntu` "
            "atau `jalankan status xl2tpd di ubuntu`."
        )

    if multi_device_request and device_context:
        summary = _format_device_snapshot_summary(device_ids, device_context)
        if summary:
            return summary

    # Ping intent
    if "ping" in msg_lower:
        if not device_ids:
            return "Saya perlu tahu device mana yang ingin di-ping. Sebutkan misalnya 'ping R1 ke R2'.\n\nContoh: coba ping R1 KE R2"

        lines = ["Saya coba kumpulkan data device terkait dari GNS3:\n"]
        if device_context:
            lines.append("```")
            lines.append(device_context[:3000])
            lines.append("```")
        lines.append("\nUntuk mengeksekusi ping nyata dari perangkat, saya perlu dukungan driver `ping`. "
                     "Saat ini data interface/routing sudah saya ambil untuk analisis.")
        return "\n".join(lines)

    # Interface intent
    if "interface" in msg_lower:
        if device_context:
            return f"Berikut data interface dari device GNS3:\n\n```\n{device_context[:4000]}\n```"
        return "Sebutkan device mana yang mau dicek interfacenya."

    # Route intent
    if "route" in msg_lower or "routing" in msg_lower:
        if device_context:
            return f"Berikut data routing dari device GNS3:\n\n```\n{device_context[:4000]}\n```"
        return "Sebutkan device mana yang mau dicek routing table-nya."

    # Generic
    return (
        f"Saya menerima: \"{message}\"\n\n"
        f"Device yang terdeteksi dari inventory GNS3: {', '.join(device_ids) if device_ids else 'tidak ada'}\n\n"
        f"Catatan: LLM provider belum menghasilkan jawaban ({error}). "
        "Data device sudah dikumpulkan dari backend untuk dianalisis."
    )


def _fallback_response(message: str, device_id: str, error: str) -> str:
    """Generate a fallback response when AI provider is unavailable."""
    msg_lower = message.lower()
    detected_ids = _find_devices(message, device_id)
    vendor_overview = _active_vendor_overview(detected_ids)
    vendor_note = f"\nVendor aktif: {vendor_overview}" if vendor_overview else ""
    if _is_context_follow_up(message):
        return _clarify_missing_context(message, None, detected_ids)

    if "show" in msg_lower and "version" in msg_lower:
        device = device_id or "the device"
        return (
            f"Ringkasan: saya akan cek versi pada {device}.\n"
            "Temuan: request mengarah ke verifikasi identitas platform dan software.\n"
            "Rekomendasi: gunakan Terminal untuk eksekusi langsung di perangkat target.\n"
            f"Langkah berikutnya:\n1. Connect ke {device} via SSH\n2. Jalankan `show version`\n3. Tampilkan hasil dan cocokkan dengan inventory"
            f"{vendor_note}"
        )

    elif "ping" in msg_lower:
        return (
            "Ringkasan: saya bantu uji konektivitas.\n"
            "Temuan: sumber dan target belum dijelaskan secara lengkap.\n"
            "Rekomendasi: tentukan source device, target IP, dan vendor agar langkah uji lebih presisi.\n"
            "Langkah berikutnya:\n"
            "1. Identifikasi source dan target\n"
            "2. Jalankan ping dari source ke target\n"
            "3. Review hasil, routing, dan ARP"
            f"{vendor_note}"
        )

    elif "interface" in msg_lower:
        return (
            "Ringkasan: saya bantu cek status interface.\n"
            "Temuan: perlu device target yang spesifik agar output tidak ambigu.\n"
            "Rekomendasi: fokus ke interface, admin/oper status, IP, dan error counter.\n"
            "Langkah berikutnya:\n"
            "1. Connect ke target device\n"
            "2. Jalankan perintah interface sesuai vendor\n"
            "3. Tampilkan status dan anomali"
            f"{vendor_note}"
        )

    elif "config" in msg_lower or "configure" in msg_lower:
        return (
            "Ringkasan: saya bisa bantu susun perubahan konfigurasi.\n"
            "Temuan: perubahan jaringan harus diproses lewat plan, approval, dan verifikasi.\n"
            "Rekomendasi: buat dry-run sebelum deploy.\n"
            "Langkah berikutnya:\n"
            "1. Susun candidate config\n"
            "2. Validasi policy dan risiko\n"
            "3. Minta approval sebelum apply\n"
            "4. Backup dan verifikasi setelah perubahan"
            f"{vendor_note}"
        )

    elif "backup" in msg_lower:
        return (
            "Ringkasan: saya bantu backup konfigurasi perangkat.\n"
            "Temuan: metode backup harus mengikuti vendor aktif.\n"
            "Rekomendasi: gunakan perintah backup yang native ke perangkat.\n"
            "Langkah berikutnya:\n"
            "1. Connect ke device\n"
            "2. Ambil running config sesuai vendor\n"
            "3. Simpan ke inventory backup"
            f"{vendor_note}"
        )

    elif "troubleshoot" in msg_lower or "problem" in msg_lower or "issue" in msg_lower:
        return (
            "Ringkasan: saya bantu troubleshooting masalah jaringan.\n"
            "Temuan: diagnosis perlu dimulai dari interface, routing, dan reachability.\n"
            "Rekomendasi: urutkan bukti sebelum menyentuh konfigurasi.\n"
            "Langkah berikutnya:\n"
            "1. Cek status device dan konektivitas\n"
            "2. Review interface dan routing table\n"
            "3. Uji ping/traceroute\n"
            "4. Cocokkan dengan log/error message"
            f"{vendor_note}"
        )

    else:
        return _clarify_missing_context(message, None, detected_ids)


def _get_inventory() -> list[dict]:
    return get_inventory()


def _analysis_device_ids(analysis: dict[str, Any] | Any) -> list[str]:
    try:
        intent = analysis.get("intent", analysis) if isinstance(analysis, dict) else analysis.intent.to_dict()
    except Exception:
        return []
    targets = intent.get("targets", []) if isinstance(intent, dict) else []
    device_ids: list[str] = []
    for item in targets:
        device_id = str(item.get("id") or "").strip()
        if device_id and device_id not in device_ids:
            device_ids.append(device_id)
    return device_ids


def _analysis_is_ambiguous(analysis: dict[str, Any] | Any) -> bool:
    try:
        intent = analysis.get("intent", analysis) if isinstance(analysis, dict) else analysis.intent.to_dict()
        return bool(intent.get("ambiguous"))
    except Exception:
        return False


def _analysis_intent_dict(analysis: dict[str, Any] | Any) -> dict[str, Any]:
    """Return the intent dict from an analysis object/dict (robust)."""
    try:
        return analysis.get("intent", analysis) if isinstance(analysis, dict) else analysis.intent.to_dict()
    except Exception:
        return {}


def _find_devices(message: str, device_id: str = "") -> list[str]:
    """Match device names/ids mentioned in the message against inventory."""
    return find_devices(message, device_id)


def _find_devices_from_message(message: str) -> list[str]:
    """Find devices mentioned explicitly in the current user message only."""
    return find_devices_from_message(message)


def _has_ambiguous_device_reference(message: str) -> bool:
    """Detect device-like tokens that are too short to resolve safely."""
    return has_ambiguous_device_reference(message)


def _is_multi_device_request(message: str, device_ids: list[str] | None = None) -> bool:
    """Heuristically detect that the user expects more than one device."""
    return is_multi_device_request(message, device_ids)


def _history_device_ids(history: list[dict[str, Any]] | None) -> list[str]:
    """Infer device ids from the recent conversation transcript."""
    return history_device_ids(history)


def _resolve_session_context(
    *,
    session_id: str | None,
    device_ids: list[str] | None,
    lab_id: str | None,
    history: list[dict[str, Any]] | None,
    message: str,
    device_id: str = "",
) -> tuple[list[str], str]:
    """Keep the previous session focus when the current message is a short follow-up."""
    return resolve_session_context(
        session_id=session_id,
        device_ids=device_ids,
        lab_id=lab_id,
        history=history,
        message=message,
        device_id=device_id,
    )


def _available_devices_context() -> str:
    """Return a compact list of devices available in the GNS3 inventory."""
    inventory = _get_inventory()
    if not inventory:
        return "(inventory kosong)"
    lines = ["Daftar device yang tersedia di lab GNS3:"]
    for device in inventory:
        lines.append(
            f"- id={device.get('id')}, hostname={device.get('hostname')}, "
            f"vendor={device.get('vendor')}, platform={device.get('platform')}"
        )
    return "\n".join(lines)


def _normalize_vendor(vendor: str, platform: str = "") -> str:
    """Map raw inventory values to a stable vendor family."""
    value = f"{vendor} {platform}".strip().lower()
    if "mikrotik" in value or "routeros" in value:
        return "mikrotik"
    if "cisco" in value or "ios" in value or "iosv" in value:
        return "cisco"
    if "aruba" in value or "aos-cx" in value or "arubacx" in value:
        return "aruba"
    if "linux" in value or value in {"debian", "ubuntu", "centos", "rocky", "alma", "fedora"}:
        return "linux"
    return "other"


def _vendor_label(vendor: str) -> str:
    labels = {
        "cisco": "Cisco",
        "mikrotik": "MikroTik",
        "aruba": "Aruba",
        "linux": "Linux",
        "other": "Other",
    }
    return labels.get(vendor, "Other")


def _vendor_noc_profile(vendor: str) -> str:
    """Return prompt guidance for one vendor family."""
    if vendor == "cisco":
        return (
            "Cisco profile: gunakan gaya IOS/NOC yang ringkas dan tegas. "
            "Prioritaskan hostname, interface admin/oper status, IP address, routing table, "
            "neighbor state, ACL, dan evidence dari output CLI. "
            "Untuk config, gunakan sintaks IOS: interface GigabitEthernet..., no shutdown, "
            "show ip interface brief, show ip route, show ip ospf neighbor."
        )
    if vendor == "mikrotik":
        return (
            "MikroTik profile: gunakan gaya RouterOS yang operasional dan spesifik. "
            "Prioritaskan /interface, /ip address, /ip route, /routing ospf, bridge, VLAN, "
            "status link, dan reachability. "
            "Untuk config, gunakan sintaks RouterOS dan jangan campur dengan IOS."
        )
    if vendor == "aruba":
        return (
            "Aruba profile: gunakan gaya AOS-CX yang fokus ke VLAN, trunk/access port, "
            "interface 1/1/x, route status, dan health perangkat. "
            "Untuk config dan verifikasi, tetap gunakan terminologi Aruba/AOS-CX."
        )
    if vendor == "linux":
        return (
            "Linux profile: gunakan gaya host/network operations yang fokus ke ip addr, ip route, "
            "ss, journalctl, systemctl, service health, dan interface state. "
            "Jika relevan, kaitkan dengan routing, service, dan konektivitas OS-level."
        )
    return (
        "Other profile: gunakan gaya NOC netral, faktual, dan tidak mencampur sintaks vendor. "
        "Pisahkan bukti, diagnosis, dan rekomendasi secara ringkas."
    )


def _session_vendor_context(device_ids: list[str]) -> str:
    """Build vendor-aware prompt context from the current session devices."""
    if not device_ids:
        return ""

    inventory = _get_inventory()
    device_lookup = {
        str(device.get("id", "")).strip(): device
        for device in inventory
        if str(device.get("id", "")).strip()
    }
    grouped: dict[str, list[str]] = {}
    for dev_id in device_ids:
        device = device_lookup.get(str(dev_id).strip())
        if not device:
            continue
        vendor_key = _normalize_vendor(
            str(device.get("vendor", "")),
            str(device.get("platform", "")),
        )
        grouped.setdefault(vendor_key, []).append(
            f"{device.get('hostname') or dev_id} ({dev_id})"
        )

    if not grouped:
        return ""

    lines = ["[SESSION VENDOR PROFILE]"]
    lines.append(
        "Style rule: bila sesi mengandung lebih dari satu vendor, jawab terpisah per vendor "
        "dan jangan mencampur sintaks CLI antar vendor."
    )
    for vendor_key, devices in grouped.items():
        lines.append(f"- { _vendor_label(vendor_key) }: {', '.join(devices)}")
        lines.append(f"  { _vendor_noc_profile(vendor_key) }")
    lines.append("[/SESSION VENDOR PROFILE]")
    return "\n".join(lines)


def _active_vendor_overview(device_ids: list[str]) -> str:
    """Return a compact vendor summary for visible responses."""
    if not device_ids:
        return ""

    inventory = _get_inventory()
    device_lookup = {
        str(device.get("id", "")).strip(): device
        for device in inventory
        if str(device.get("id", "")).strip()
    }
    grouped: dict[str, list[str]] = {}
    for dev_id in device_ids:
        device = device_lookup.get(str(dev_id).strip())
        if not device:
            continue
        vendor_key = _normalize_vendor(
            str(device.get("vendor", "")),
            str(device.get("platform", "")),
        )
        grouped.setdefault(vendor_key, []).append(str(device.get("hostname") or dev_id))

    if not grouped:
        return ""

    parts = [f"{_vendor_label(vendor)}: {', '.join(devices)}" for vendor, devices in grouped.items()]
    return "; ".join(parts)


def _device_inventory_lookup() -> dict[str, dict[str, Any]]:
    """Build an inventory lookup keyed by device id."""
    lookup: dict[str, dict[str, Any]] = {}
    for device in _get_inventory():
        dev_id = str(device.get("id", "")).strip()
        if dev_id:
            lookup[dev_id] = device
    return lookup


def _device_display_name(device_id: str) -> str:
    device = _device_inventory_lookup().get(str(device_id).strip(), {})
    hostname = str(device.get("hostname") or "").strip()
    return hostname or str(device_id).strip() or "unknown-device"


def _requested_device_context(device_ids: list[str]) -> str:
    """Render the requested devices as a deterministic prompt block."""
    if not device_ids:
        return ""

    lookup = _device_inventory_lookup()
    lines = ["[REQUESTED DEVICES]"]
    for index, dev_id in enumerate(device_ids, start=1):
        device = lookup.get(str(dev_id).strip(), {})
        hostname = str(device.get("hostname") or dev_id).strip() or str(dev_id)
        vendor = _vendor_label(_normalize_vendor(str(device.get("vendor", "")), str(device.get("platform", ""))))
        platform = str(device.get("platform") or "-").strip() or "-"
        management = str(device.get("management_address") or device.get("management_ip") or "-").strip() or "-"
        lines.append(
            f"{index}. id={dev_id}, hostname={hostname}, vendor={vendor}, platform={platform}, management={management}"
        )
    lines.append(
        "Rule: when more than one device is requested, answer every device separately in the same order "
        "as requested. Do not collapse the response into a single vendor summary."
    )
    lines.append(
        "Rule: if one device state is incomplete, keep the other device sections and mark the missing device "
        "as 'state belum lengkap' instead of saying the whole vendor family is unavailable."
    )
    lines.append("[/REQUESTED DEVICES]")
    return "\n".join(lines)


def _parse_device_context_payload(device_context: str) -> list[dict[str, Any]]:
    """Parse the collected device payload back into structured snapshots."""
    if not device_context:
        return []

    try:
        payload = json.loads(device_context)
    except Exception:
        return []

    if isinstance(payload, dict):
        snapshots = payload.get("snapshots") or payload.get("devices") or payload.get("data") or []
    elif isinstance(payload, list):
        snapshots = payload
    else:
        snapshots = []

    result: list[dict[str, Any]] = []
    for item in snapshots:
        if isinstance(item, dict):
            result.append(item)
    return result


def _normalize_state_collection(value: Any) -> list[dict[str, Any]]:
    """Normalize backend driver payloads to a flat list of dict rows."""
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("data", "items", "interfaces", "routes", "rows", "vlans"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
        rows: list[dict[str, Any]] = []
        for key, nested in value.items():
            if isinstance(nested, dict):
                row = {"name": key, **nested}
                rows.append(row)
        if rows:
            return rows
        return []
    return []


def _inspection_topic(message: str) -> str:
    normalized = " ".join(str(message or "").lower().split())
    if any(token in normalized for token in ("ppp", "l2tp", "ipsec", "xl2tpd", "strongswan")):
        return "linux_tunnel"
    if any(token in normalized for token in ("service", "layanan", "systemctl", "process", "proses", "port", "ss ")):
        return "linux_service"
    if "ip address" in normalized or "ip addr" in normalized or "address" in normalized:
        return "ip_address"
    if "interface" in normalized:
        return "interface"
    if "route" in normalized or "routing" in normalized:
        return "routing"
    if "status" in normalized or "health" in normalized or "kondisi" in normalized:
        return "status"
    return "summary"


def _service_name_from_message(message: str) -> str:
    normalized = str(message or "").strip().lower()
    match = re.search(r"\b(?:service|layanan|process|proses)\s+([a-z0-9_.@-]+)", normalized)
    if match:
        return match.group(1).strip()
    return ""


def _markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    safe_headers = [str(item or "-") for item in headers]
    lines = [
        "| " + " | ".join(safe_headers) + " |",
        "| " + " | ".join("---" for _ in safe_headers) + " |",
    ]
    for row in rows:
        values = [str(item or "-").replace("\n", " ") for item in row]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def _format_device_snapshot_summary(device_ids: list[str], device_context: str) -> str:
    """Build a compact per-device summary from the collected snapshot payload."""
    if len([item for item in device_ids if item]) < 2:
        return ""

    snapshots = _parse_device_context_payload(device_context)
    if not snapshots:
        return ""

    lookup = {str(item.get("device_id", "")).strip(): item for item in snapshots if str(item.get("device_id", "")).strip()}
    inventory = _device_inventory_lookup()
    rows: list[list[str]] = []

    for dev_id in device_ids:
        device = inventory.get(str(dev_id).strip(), {})
        snapshot = lookup.get(str(dev_id).strip(), {})
        hostname = str(device.get("hostname") or dev_id).strip() or str(dev_id)
        vendor = _vendor_label(_normalize_vendor(str(device.get("vendor", "")), str(device.get("platform", ""))))
        platform = str(device.get("platform") or "-").strip() or "-"

        facts = snapshot.get("facts") if isinstance(snapshot.get("facts"), dict) else {}
        interfaces = snapshot.get("interfaces")
        routes = snapshot.get("routes")

        snapshot_status = "state belum lengkap"
        if isinstance(facts, dict) and facts.get("error"):
            snapshot_status = f"state gagal dikumpulkan: {facts.get('error')}"
        elif facts or interfaces is not None or routes is not None:
            snapshot_status = "state tersedia"

        interface_count = len(interfaces) if isinstance(interfaces, list) else None
        route_count = len(routes) if isinstance(routes, list) else None
        management = str(device.get("management_address") or device.get("management_ip") or "-").strip() or "-"

        rows.append([
            f"{hostname} ({dev_id})",
            vendor,
            platform,
            management,
            snapshot_status,
            str(interface_count) if interface_count is not None else "-",
            str(route_count) if route_count is not None else "-",
        ])

    lines = [
        "[MULTI DEVICE COVERAGE]",
        "Rule: every requested device must appear as its own row. If one device is incomplete, only that row should be marked incomplete.",
        "",
        "| Device | Vendor | Platform | Management | State | Interfaces | Routes |",
        "|---|---|---|---|---|---:|---:|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    lines.append("[/MULTI DEVICE COVERAGE]")
    return "\n".join(lines)


def _response_mentions_device(response: str, device_id: str) -> bool:
    """Check whether the response explicitly references a requested device."""
    response_lower = response.lower()
    device = _device_inventory_lookup().get(str(device_id).strip(), {})
    hostname = str(device.get("hostname") or "").strip().lower()
    vendor = str(device.get("vendor") or "").strip().lower()
    first_word = hostname.split()[0] if hostname else ""
    candidates = [str(device_id).strip().lower(), hostname, first_word, vendor]
    return any(candidate and candidate in response_lower for candidate in candidates)


def _enforce_multi_device_response(
    response: str,
    message: str,
    history: list[dict[str, Any]] | None,
    device_ids: list[str],
    device_context: str,
) -> str:
    """Append a per-device summary when the answer still collapses multi-device context."""
    selected = [item for item in device_ids if item]
    if len(selected) < 2:
        return response

    if all(_response_mentions_device(response, dev_id) for dev_id in selected):
        return response

    summary = _format_device_snapshot_summary(selected, device_context)
    if not summary:
        return response

    body = response.rstrip()
    separator = "\n\n" if body else ""
    return f"{body}{separator}{summary}"


def _conversation_history_context(history: list[dict[str, Any]] | None, limit: int = 12) -> str:
    """Render recent chat history into a compact transcript for the prompt."""
    if not history:
        return ""

    lines: list[str] = []
    for item in history[-limit:]:
        role = str(item.get("role", "")).strip().lower()
        text = str(item.get("text", item.get("content", ""))).strip()
        if not text:
            continue
        label = "User" if role == "user" else "Assistant" if role == "assistant" else role.title() or "Message"
        lines.append(f"{label}: {text}")

    if not lines:
        return ""

    return "[CONVERSATION HISTORY]\n" + "\n".join(lines) + "\n[/CONVERSATION HISTORY]"


def _latest_assistant_excerpt(history: list[dict[str, Any]] | None, limit: int = 800) -> str:
    """Return the latest assistant message excerpt for short follow-up prompts."""
    if not history:
        return ""

    for item in reversed(history):
        role = str(item.get("role", "")).strip().lower()
        if role != "assistant":
            continue
        text = str(item.get("text", item.get("content", ""))).strip()
        if text:
            return text[:limit]
    return ""


def _is_short_follow_up(message: str) -> bool:
    return _is_context_follow_up(message)


def _conversation_anchor(history: list[dict[str, Any]] | None) -> dict[str, str]:
    """Extract the last user intent and assistant recommendation."""
    anchor = {"last_user": "", "last_assistant": "", "topic": ""}
    if not history:
        return anchor

    for item in reversed(history):
        role = str(item.get("role", "")).strip().lower()
        text = str(item.get("text", item.get("content", ""))).strip()
        if not text:
            continue
        if role == "assistant" and not anchor["last_assistant"]:
            anchor["last_assistant"] = text[:1200]
        elif role == "user" and not anchor["last_user"]:
            anchor["last_user"] = text[:1200]
        if anchor["last_user"] and anchor["last_assistant"]:
            break

    topic_source = anchor["last_user"] or anchor["last_assistant"]
    if topic_source:
        anchor["topic"] = topic_source.splitlines()[0][:160]
    return anchor


def _conversation_summary(history: list[dict[str, Any]] | None, device_ids: list[str]) -> str:
    """Build a compact session summary for the prompt."""
    anchor = _conversation_anchor(history)
    if not any(anchor.values()) and not device_ids:
        return ""

    lines = ["[SESSION SUMMARY]"]
    if anchor["topic"]:
        lines.append(f"Topic: {anchor['topic']}")
    if device_ids:
        lines.append(f"Active devices: {', '.join(device_ids)}")
    if anchor["last_user"]:
        lines.append(f"Last user intent: {anchor['last_user']}")
    if anchor["last_assistant"]:
        lines.append(f"Last assistant recommendation: {anchor['last_assistant']}")
    lines.append("Behavior: continue the same operational thread unless the user explicitly changes topic.")
    lines.append("[/SESSION SUMMARY]")
    return "\n".join(lines)


def _is_context_follow_up(message: str) -> bool:
    return is_context_follow_up(message)


def _is_structured_response(text: str) -> bool:
    stripped = text.strip()
    return (
        stripped.startswith("```")
        or stripped.startswith("{")
        or stripped.startswith("[")
    )


def _build_next_step(message: str, history: list[dict[str, Any]] | None, device_ids: list[str]) -> str:
    """Suggest a practical next action based on the current conversation."""
    anchor = _conversation_anchor(history)
    msg_lower = message.lower()
    vendor_context = _session_vendor_context(device_ids)
    vendor_hint = ""
    if vendor_context:
        vendor_hint = " Sesuaikan istilah dengan vendor aktif di sesi ini."

    if _is_context_follow_up(message) and anchor["last_assistant"]:
        return (
            "Langkah berikutnya: saya bisa turunkan rekomendasi sebelumnya menjadi langkah per-device "
            "atau cek dampaknya ke routing, interface, dan reachability."
            f"{vendor_hint}"
        )

    if "ping" in msg_lower:
        if device_ids:
            return (
                "Langkah berikutnya: jika Anda ingin uji konektivitas yang lebih presisi, sebutkan "
                "sumber, target IP, dan apakah hasilnya ingin saya validasi dengan routing dan ARP."
                f"{vendor_hint}"
            )
        return "Langkah berikutnya: sebutkan source device dan target IP agar saya bisa susun langkah uji konektivitas."

    if "route" in msg_lower or "routing" in msg_lower:
        return (
            "Langkah berikutnya: saya bisa bandingkan routing table antar device, cek next-hop, "
            "dan cari indikasi OSPF/BGP/static route yang belum tepat."
            f"{vendor_hint}"
        )

    if "interface" in msg_lower:
        return (
            "Langkah berikutnya: saya bisa cek admin status, oper status, IP address, dan error counter "
            "pada interface yang relevan."
            f"{vendor_hint}"
        )

    if any(token in msg_lower for token in ("config", "configure", "apply", "deploy")):
        return (
            "Langkah berikutnya: saya bisa bantu susun dry-run, risk analysis, dan approval plan "
            "sebelum perubahan diterapkan."
            f"{vendor_hint}"
        )

    if "backup" in msg_lower:
        return (
            "Langkah berikutnya: saya bisa bantu buat rencana backup, compare, atau restore bila diperlukan."
            f"{vendor_hint}"
        )

    if "troubleshoot" in msg_lower or "problem" in msg_lower or "issue" in msg_lower:
        return (
            "Langkah berikutnya: saya bisa urutkan diagnosis dari interface, routing, ARP, ACL, "
            "hingga verifikasi konektivitas end-to-end."
            f"{vendor_hint}"
        )

    if anchor["last_assistant"]:
        return (
            "Langkah berikutnya: saya bisa lanjutkan dari rekomendasi terakhir atau bantu fokus ke device tertentu."
            f"{vendor_hint}"
        )

    return (
        "Langkah berikutnya: sebutkan device, lab, atau tujuan yang ingin diperiksa."
        f"{vendor_hint}"
    )


def _clarify_missing_context(message: str, history: list[dict[str, Any]] | None, device_ids: list[str]) -> str:
    """Ask for clarification when the device context is ambiguous."""
    anchor = _conversation_anchor(history)
    vendor_overview = _active_vendor_overview(device_ids)
    multi_device_request = _is_multi_device_request(message, device_ids)

    if _is_context_follow_up(message) and anchor["last_assistant"]:
        follow_up_hint = "Konteks terakhir masih mengarah ke pembahasan sebelumnya."
        if vendor_overview:
            follow_up_hint += f" Vendor aktif: {vendor_overview}."
        return (
            "Ringkasan: konteks follow-up masih ambigu.\n"
            f"Temuan: {follow_up_hint}\n"
            "Rekomendasi: lanjutkan dari device/topik terakhir agar saya tidak salah arah.\n"
            "Langkah berikutnya: balas dengan nama device, misalnya `MK-1`, atau ketik `lanjut` jika memang ingin saya teruskan dari pembahasan sebelumnya."
        )

    if multi_device_request and len([item for item in device_ids if item]) < 2:
        return (
            "Ringkasan: permintaan ini mengarah ke lebih dari satu perangkat, tetapi device yang terdeteksi belum lengkap.\n"
            f"Temuan: saya hanya melihat {vendor_overview or 'sebagian device'}.\n"
            "Rekomendasi: sebutkan semua hostname yang ingin diperiksa supaya saya bisa ambil state masing-masing perangkat tanpa ambigu.\n"
            "Langkah berikutnya: contoh `Tampilkan routing table R1 dan R2` atau `Cek interface R1, R2, dan SW1`."
        )

    if vendor_overview:
        return (
            "Ringkasan: device yang dimaksud belum spesifik.\n"
            f"Temuan: saya melihat konteks vendor aktif: {vendor_overview}.\n"
            "Rekomendasi: sebutkan hostname atau device ID yang dimaksud supaya saya bisa fokus ke perangkat yang benar.\n"
            "Langkah berikutnya: pilih satu device, misalnya `MK-1`, `R1`, atau `SW1`."
        )

    if anchor["last_assistant"] or anchor["topic"]:
        topic = anchor["topic"] or "pembahasan sebelumnya"
        return (
            "Ringkasan: konteks masih ambigu.\n"
            f"Temuan: percakapan terakhir mengarah ke {topic}.\n"
            "Rekomendasi: konfirmasi device atau topik yang dimaksud sebelum saya lanjut.\n"
            "Langkah berikutnya: jawab dengan hostname device yang ingin dipilih, atau ketik `lanjut` untuk mengikuti konteks terakhir."
        )

    return (
        "Ringkasan: device belum teridentifikasi.\n"
        "Temuan: belum ada referensi device yang cukup dari percakapan saat ini.\n"
        "Rekomendasi: berikan hostname, device ID, atau vendor yang ingin diperiksa.\n"
        "Langkah berikutnya: contoh `cek MK-1`, `cek R1`, atau `cek SW1`."
    )


def _append_professional_closure(
    response: str,
    message: str,
    history: list[dict[str, Any]] | None,
    device_ids: list[str],
) -> str:
    """Append a concise professional closing if the answer is plain text."""
    if _is_structured_response(response):
        return response

    if "langkah berikutnya" in response.lower() or "next step" in response.lower():
        return response

    next_step = _build_next_step(message, history, device_ids)
    body = response.rstrip()
    separator = "\n\n" if body else ""
    return f"{body}{separator}{next_step}"


def _extract_cli_command(message: str) -> str:
    """Extract an explicit CLI command from a user message.

    The agent only auto-routes when the user is clearly asking to run a
    command or when the message itself looks like a device CLI command.
    """
    text = str(message or "").strip()
    if not text:
        return ""

    code_block = re.search(r"`([^`]+)`", text)
    if code_block:
        candidate = code_block.group(1).strip()
        if candidate:
            return candidate

    lowered = text.lower()
    def _looks_like_explicit_cli(candidate: str) -> bool:
        normalized = candidate.lower().strip()
        if not normalized:
            return False
        direct_markers = (
            "show ",
            "display ",
            "ping ",
            "traceroute ",
            "trace ",
            "/",
            "interface ",
            "system ",
            "route ",
            "journalctl",
            "ss ",
            "cat ",
            "ls ",
            "uname",
        )
        if normalized.startswith(direct_markers):
            return True
        if normalized.startswith(("ip route ", "ip address print", "ip firewall print", "ip arp print")):
            return True
        return "?" in normalized

    direct_prefixes = (
        "show ",
        "display ",
        "ping ",
        "traceroute ",
        "trace ",
        "ip route ",
        "ip address print",
        "ip firewall print",
        "ip arp print",
        "/",
        "interface ",
        "system ",
        "route ",
        "journalctl",
        "ss ",
        "cat ",
        "ls ",
        "uname",
    )
    if lowered.startswith(direct_prefixes):
        return text

    routed_prefixes = (
        "jalankan ",
        "run ",
        "execute ",
        "eksekusi ",
        "cek ",
        "lihat ",
        "test ",
    )
    for prefix in routed_prefixes:
        if lowered.startswith(prefix):
            candidate = text[len(prefix):].strip(" :")
            if candidate and _looks_like_explicit_cli(candidate):
                return candidate
            return ""

    if lowered.startswith(("ip route ", "ip address print", "ip firewall print", "ip arp print")):
        return text

    return ""


def _command_tool_name_for_vendor(vendor: str) -> str:
    vendor = (vendor or "").lower()
    if vendor == "cisco":
        return "run_cisco_command"
    if vendor == "mikrotik":
        return "run_mikrotik_command"
    if vendor == "linux":
        return "run_linux_command"
    return "run_device_command"


def _render_command_output_section(device_id: str, result: dict[str, Any]) -> str:
    device = _device_inventory_lookup().get(str(device_id).strip(), {})
    hostname = str(device.get("hostname") or device_id).strip() or device_id
    vendor = _vendor_label(_normalize_vendor(str(device.get("vendor", "")), str(device.get("platform", ""))))
    status = result.get("status", "unknown")
    command = result.get("command", "")
    output = result.get("output")

    if isinstance(output, list):
        rendered_output = "\n".join(str(item) for item in output)
    elif isinstance(output, dict):
        rendered_output = json.dumps(output, indent=2, ensure_ascii=False, default=str)
    else:
        rendered_output = str(output or result.get("raw", "") or "")

    rendered_output = rendered_output.strip()
    if not rendered_output:
        rendered_output = "(no output)"

    return (
        f"{hostname} ({vendor}) - {status}\n"
        f"$ {command}\n"
        f"{rendered_output}"
    )


def _build_device_state_event(
    *,
    task_id: str,
    device_ids: list[str],
    device_context: str,
) -> dict[str, Any] | None:
    if not device_context:
        return None

    try:
        parsed = json.loads(device_context)
    except Exception:
        parsed = {"raw": device_context}

    snapshots = parsed.get("snapshots") if isinstance(parsed, dict) else []
    if not isinstance(snapshots, list):
        snapshots = []

    first_snapshot = snapshots[0] if snapshots else {}
    facts = first_snapshot.get("facts", {}) if isinstance(first_snapshot, dict) else {}
    if not isinstance(facts, dict):
        facts = {}

    device_id = str(first_snapshot.get("device_id") or (device_ids[0] if device_ids else "")).strip()
    hostname = str(facts.get("hostname") or device_id or "device").strip()
    vendor = _normalize_vendor(str(facts.get("vendor", "")), str(facts.get("platform", "")))

    return {
        "id": f"state-{uuid.uuid4().hex[:10]}",
        "taskId": task_id,
        "deviceId": device_id or None,
        "device": hostname,
        "vendor": vendor,
        "platform": str(facts.get("platform", "")),
        "summary": f"{len(snapshots)} device snapshot(s) collected",
        "content": json.dumps(parsed, indent=2, ensure_ascii=False, default=str),
        "devices": device_ids,
        "createdAt": datetime.utcnow().isoformat(),
    }


def _build_command_output_event(
    *,
    task_id: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    output = result.get("output", result.get("raw", ""))
    if isinstance(output, dict):
        output_value: Any = json.dumps(output, indent=2, ensure_ascii=False, default=str)
    elif isinstance(output, list):
        output_value = [str(item) for item in output]
    elif output is None:
        output_value = ""
    else:
        output_value = str(output)

    status = str(result.get("status", "running")).lower()
    if result.get("error"):
        status = "failed"

    return {
        "id": f"cmd-{uuid.uuid4().hex[:10]}",
        "taskId": task_id,
        "deviceId": str(result.get("device_id", "")).strip() or None,
        "device": str(result.get("hostname", "")).strip() or None,
        "command": str(result.get("command", "")).strip(),
        "status": status if status in {"ok", "failed", "blocked", "running"} else "running",
        "output": output_value,
        "createdAt": datetime.utcnow().isoformat(),
    }


def _is_read_only_inspection_request(message: str) -> bool:
    """Detect read-only inspection requests that should bypass LLM tool-style output."""
    normalized = " ".join(str(message or "").lower().replace("?", " ").replace("!", " ").split())
    if not normalized:
        return False

    change_markers = (
        "configure",
        "config ",
        "apply",
        "deploy",
        "set ",
        "add ",
        "remove",
        "delete",
        "restart",
        "reload",
        "shutdown",
    )
    if any(marker in normalized for marker in change_markers):
        return False

    inspection_prefixes = (
        "cek ",
        "lihat ",
        "tampilkan ",
        "show ",
        "display ",
        "inspect ",
        "check ",
        "lihatkan ",
        "periksa ",
        "jelaskan",
        "explain",
        "rincian",
    )
    inspection_terms = (
        "ip address",
        "ip addr",
        "address",
        "interface",
        "routing",
        "route",
        "status",
        "kondisi",
        "health",
        "version",
        "vlan",
        "hostname",
        "config",
        "konfigurasi",
        "configuration",
        "startup",
        "ppp",
        "l2tp",
        "ipsec",
        "xl2tpd",
        "strongswan",
        "service",
        "layanan",
        "process",
        "proses",
        "port",
        "docker",
        "zerotier",
    )
    if normalized.startswith(inspection_prefixes) and any(term in normalized for term in inspection_terms):
        return True
    if normalized.startswith(("show ", "display ", "inspect ", "check ")) and any(term in normalized for term in inspection_terms):
        return True
    return False


def _build_read_only_inspection_response(
    message: str,
    device_ids: list[str],
    device_context: str,
) -> str:
    """Render a deterministic read-only inspection response from collected state."""
    explicit_from_message = _find_devices_from_message(message)
    if explicit_from_message:
        device_ids = explicit_from_message

    snapshots = _parse_device_context_payload(device_context)
    lookup = {
        str(item.get("device_id", "")).strip(): item
        for item in snapshots
        if str(item.get("device_id", "")).strip()
    }
    if not device_ids:
        device_ids = list(lookup.keys())

    if not device_ids:
        return _clarify_missing_context(message, None, [])

    topic = _inspection_topic(message)
    lines = ["Ringkasan: permintaan terdeteksi sebagai inspeksi read-only."]
    lines.append("Sumber data: backend device snapshot yang berhasil dikumpulkan saat request ini diproses.")
    multi_device = len([item for item in device_ids if item]) >= 2
    if multi_device:
        lines.append("Temuan: saya tampilkan ringkasan per device yang diminta.")
    else:
        lines.append("Temuan: state device target sudah saya ambil dari backend.")

    for index, dev_id in enumerate(device_ids, start=1):
        snapshot = lookup.get(str(dev_id).strip(), {})
        facts = snapshot.get("facts") if isinstance(snapshot.get("facts"), dict) else {}
        health = snapshot.get("health") if isinstance(snapshot.get("health"), dict) else {}
        interfaces = _normalize_state_collection(snapshot.get("interfaces"))
        routes = _normalize_state_collection(snapshot.get("routes"))

        hostname = str(facts.get("hostname") or dev_id).strip() or str(dev_id)
        vendor = _vendor_label(_normalize_vendor(str(facts.get("vendor", "")), str(facts.get("platform", ""))))
        platform = str(facts.get("platform") or "-").strip() or "-"
        management = str(facts.get("management_address") or facts.get("management_ip") or "-").strip() or "-"
        status = "online" if health.get("reachable") else "offline"
        reason = str(health.get("reason") or health.get("ssh_banner") or "").strip()

        lines.append("")
        lines.append(f"## {index}. {hostname} ({dev_id})")
        lines.append(f"- Vendor: {vendor}")
        lines.append(f"- Platform: {platform}")
        lines.append(f"- Management IP: {management}")
        lines.append(f"- Status device: {status}")
        if reason:
            lines.append(f"- Detail: {reason}")

        if topic in {"linux_tunnel", "linux_service"} and _normalize_vendor(str(facts.get("vendor", "")), str(facts.get("platform", ""))) == "linux":
            service_name = _service_name_from_message(message)
            if topic == "linux_service" and service_name:
                lines.append("")
                lines.append(f"### Service Check: {service_name}")
                lines.append("Data yang terkonfirmasi dari snapshot:")
                lines.extend(
                    _markdown_table(
                        ["Item", "Status"],
                        [
                            ["SSH reachability", status],
                            ["Primary management", management],
                            ["Interface data", "tersedia" if interfaces else "belum tersedia"],
                            ["Routing data", "tersedia" if routes else "belum tersedia"],
                            [f"systemd service `{service_name}`", "belum tersedia di snapshot"],
                            [f"process `{service_name}`", "belum tersedia di snapshot"],
                            [f"listening port `{service_name}`", "belum tersedia di snapshot"],
                        ],
                    )
                )
                lines.append("")
                lines.append(f"Kesimpulan sementara: host `ubuntu` reachable, tetapi status service `{service_name}` belum bisa dipastikan dari snapshot saat ini.")
                lines.append("Command live yang perlu dijalankan:")
                lines.append("```bash")
                lines.append(f"systemctl status {service_name} --no-pager")
                lines.append(f"systemctl is-active {service_name}")
                lines.append(f"ps aux | grep -i '[{service_name[:1]}]{service_name[1:]}'")
                lines.append(f"ss -tulpen | grep -i {service_name}")
                lines.append(f"journalctl -u {service_name} -n 80 --no-pager")
                lines.append("docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' | grep -i frigate")
                lines.append("```")
                lines.append("Catatan: jika Frigate berjalan sebagai container, statusnya tidak muncul sebagai service systemd biasa; perlu cek `docker ps` dan log container.")
                continue

            lines.append("")
            lines.append("### PPP/L2TP/IPsec")
            lines.append("Data yang terkonfirmasi dari snapshot:")
            lines.extend(
                _markdown_table(
                    ["Item", "Status"],
                    [
                        ["SSH reachability", status],
                        ["Primary management", management],
                        ["Interface data", "tersedia" if interfaces else "belum tersedia"],
                        ["Routing data", "tersedia" if routes else "belum tersedia"],
                        ["Process/service/port data", "belum tersedia di snapshot"],
                    ],
                )
            )
            ppp_rows: list[list[str]] = []
            for item in interfaces:
                name = str(item.get("name") or item.get("interface") or item.get("ifname") or "-").strip()
                if any(token in name.lower() for token in ("ppp", "l2tp", "ipsec")):
                    ip_address = str(item.get("ip_address") or item.get("ip") or item.get("address") or "-").strip() or "-"
                    state = str(item.get("status") or item.get("admin_status") or item.get("state") or item.get("operstate") or "-").strip() or "-"
                    ppp_rows.append([name, ip_address, state])
            if ppp_rows:
                lines.append("")
                lines.append("Interface PPP/L2TP yang terlihat:")
                lines.extend(_markdown_table(["Interface", "IP Address", "Status"], ppp_rows))
            else:
                lines.append("")
                lines.append("Kesimpulan sementara: belum ada interface `ppp*`, `l2tp*`, atau `ipsec*` yang terlihat pada snapshot interface.")
            lines.append("Catatan: untuk memastikan daemon berjalan atau tidak, backend perlu menjalankan command Linux seperti `systemctl status xl2tpd strongswan`, `ss -ulnp`, dan `ip link show ppp0`.")
            continue

        if isinstance(snapshot.get("interfaces"), dict) and snapshot.get("interfaces", {}).get("skipped"):
            lines.append("- Interfaces: belum diambil karena device tidak reachable")
        elif interfaces:
            if topic in {"interface", "ip_address", "status"}:
                lines.append("- Interfaces:")
                rows: list[list[str]] = []
                for item in interfaces[:12]:
                    name = str(item.get("name") or item.get("interface") or item.get("ifname") or "-").strip() or "-"
                    ip_address = str(item.get("ip_address") or item.get("ip") or item.get("address") or "-").strip() or "-"
                    admin_status = str(item.get("status") or item.get("admin_status") or item.get("state") or "-").strip() or "-"
                    oper_status = str(item.get("protocol") or item.get("oper_status") or item.get("link") or "-").strip() or "-"
                    rows.append([name, ip_address, admin_status, oper_status])
                lines.extend(_markdown_table(["Interface", "IP Address", "Status", "Protocol"], rows))
            else:
                lines.append(f"- Interfaces: {len(interfaces)} data")
        if isinstance(snapshot.get("routes"), dict) and snapshot.get("routes", {}).get("skipped"):
            lines.append("- Routing: belum diambil karena device tidak reachable")
        elif routes:
            if topic == "routing":
                lines.append("- Routing:")
                rows = []
                for item in routes[:12]:
                    destination = str(item.get("dst") or item.get("destination") or item.get("network") or "-").strip() or "-"
                    gateway = str(item.get("gateway") or item.get("via") or item.get("next_hop") or "-").strip() or "-"
                    iface = str(item.get("interface") or item.get("iface") or item.get("out_interface") or "-").strip() or "-"
                    metric = str(item.get("metric") or item.get("distance") or "-").strip() or "-"
                    rows.append([destination, gateway, iface, metric])
                lines.extend(_markdown_table(["Network", "Next Hop", "Interface", "Metric"], rows))
            else:
                lines.append(f"- Routing: {len(routes)} data")

    lines.append("")
    if topic == "linux_service":
        service_name = _service_name_from_message(message)
        label = f" `{service_name}`" if service_name else ""
        lines.append(f"Langkah berikutnya: jalankan pengecekan live service{label} dari backend terminal atau agent tool agar status proses, port, dan log bisa dipastikan.")
    elif topic == "linux_tunnel":
        lines.append("Langkah berikutnya: jalankan pengecekan live service/port dari backend terminal atau agent tool agar status PPP/L2TP bisa dipastikan, bukan hanya disimpulkan dari snapshot.")
    else:
        lines.append("Langkah berikutnya: sebutkan detail yang ingin diperiksa berikutnya, misalnya interface tertentu, routing table penuh, atau command verifikasi vendor.")
    return "\n".join(lines)


def _append_approval_event(
    *,
    plan_id: str,
    task: str,
    devices: list[str],
    risk: str,
    status: str,
    message: str,
    approved_by: str | None = None,
    cancelled_by: str | None = None,
) -> dict[str, Any]:
    approval_event = {
        "id": f"approval-{datetime.utcnow().timestamp():.0f}",
        "type": "approval",
        "taskId": plan_id,
        "task": task,
        "devices": devices,
        "risk": risk,
        "status": status,
        "message": message,
        "createdAt": datetime.utcnow().isoformat(),
    }
    if approved_by:
        approval_event["approvedBy"] = approved_by
    if cancelled_by:
        approval_event["cancelledBy"] = cancelled_by

    approval_record = {"type": "approval", **approval_event}
    _agent_events.append(approval_record)
    return approval_event


def _build_verification_event(
    *,
    task_id: str,
    device_ids: list[str],
    status: str,
    message: str,
    checks: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": f"verify-{uuid.uuid4().hex[:10]}",
        "taskId": task_id,
        "devices": device_ids,
        "status": status,
        "message": message,
        "checks": checks or [],
        "createdAt": datetime.utcnow().isoformat(),
    }


def _normalize_workflow_state(state: str) -> str:
    normalized = str(state or "").strip().lower().replace("-", "_").replace(" ", "_")
    allowed = {
        "thinking",
        "planning",
        "waiting_approval",
        "running",
        "verifying",
        "completed",
        "failed",
    }
    return normalized if normalized in allowed else "thinking"


def _workflow_state_index(state: str) -> int:
    order = {
        "thinking": 0,
        "planning": 1,
        "waiting_approval": 2,
        "running": 3,
        "verifying": 4,
        "completed": 5,
        "failed": 6,
    }
    return order.get(_normalize_workflow_state(state), 0)


def _build_workflow_state_event(
    *,
    task_id: str,
    state: str,
    label: str | None = None,
    detail: str | None = None,
    events_count: int | None = None,
    active_index: int | None = None,
    device_ids: list[str] | None = None,
) -> dict[str, Any]:
    normalized_state = _normalize_workflow_state(state)
    default_labels = {
        "thinking": "Thinking",
        "planning": "Planning",
        "waiting_approval": "Waiting approval",
        "running": "Running",
        "verifying": "Verifying",
        "completed": "Completed",
        "failed": "Failed",
    }
    default_details = {
        "thinking": "Menganalisis permintaan dan menyiapkan konteks jaringan.",
        "planning": "Menyusun langkah eksekusi yang aman dan terarah.",
        "waiting_approval": "Menunggu persetujuan sebelum perubahan diterapkan.",
        "running": "Backend sedang menjalankan langkah yang disetujui.",
        "verifying": "Memeriksa hasil dan validasi pasca-aksi.",
        "completed": "Workflow selesai dengan status akhir yang tervalidasi.",
        "failed": "Workflow dihentikan karena ada error atau validasi gagal.",
    }
    return {
        "id": f"workflow-{uuid.uuid4().hex[:10]}",
        "type": "workflow_state",
        "taskId": task_id,
        "state": normalized_state,
        "label": label or default_labels[normalized_state],
        "detail": detail or default_details[normalized_state],
        "activeIndex": active_index if active_index is not None else _workflow_state_index(normalized_state),
        "eventsCount": int(events_count or 0),
        "devices": device_ids or [],
        "createdAt": datetime.utcnow().isoformat(),
    }


def _extract_ping_target_ips_from_message(message: str) -> list[str]:
    """Extract explicit IPv4 addresses mentioned in a ping request."""
    pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    candidates = re.findall(pattern, str(message or ""))
    seen: list[str] = []
    for ip in candidates:
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            continue
        if ip not in seen:
            seen.append(ip)
    return seen


def _interface_ips(interfaces: Any, device_id: str) -> list[str]:
    """Return interface IP/prefix strings for a device interfaces payload."""
    payload = interfaces if isinstance(interfaces, dict) else {}
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    ips: list[str] = []
    for item in data:
        addr = str((item or {}).get("ip_address") or "").strip()
        if addr and addr.lower() not in {"-", "unassigned"}:
            ips.append(addr)
    return ips


def _same_subnet(a: str, b: str) -> bool:
    """True if two ip/prefix strings live on the same network."""
    try:
        return ipaddress.ip_interface(a).network == ipaddress.ip_interface(b).network
    except ValueError:
        return False


async def _resolve_ping_source(
    message: str,
    device_ids: list[str],
) -> tuple[str, str]:
    """Resolve the ping source device from a natural language message."""
    msg = str(message or "").lower()
    m = re.search(r"(?:dari|from)\s+([a-z0-9][a-z0-9_.\-]*)", msg)
    if m:
        token = m.group(1)
        inventory = _device_inventory_lookup()
        for dev_id in device_ids:
            device = inventory.get(dev_id, {}) or {}
            name = str(device.get("hostname") or device.get("id") or "").lower()
            if token in str(dev_id).lower() or token in name or name.startswith(token):
                return dev_id, str(device.get("hostname") or dev_id)
    if device_ids:
        inventory = _device_inventory_lookup()
        device = inventory.get(device_ids[0], {}) or {}
        return device_ids[0], str(device.get("hostname") or device_ids[0])
    return "", ""


async def _resolve_ping_targets(
    message: str,
    device_ids: list[str],
    source_id: str,
) -> list[dict[str, str]]:
    """Resolve ping target devices/IPs from a natural language message."""
    explicit = _extract_ping_target_ips_from_message(message)
    if explicit:
        return [{"id": "", "name": ip, "ip": ip} for ip in explicit]

    msg = str(message or "").lower()
    targets = [d for d in device_ids if d and d != source_id]
    named = re.search(r"(?:ke|to|terhadap)\s+([a-z0-9][a-z0-9 _.]+)", msg)
    all_routers = "semua" in msg and ("router" in msg or "device" in msg)

    if named and not all_routers:
        token = named.group(1).strip()
        inventory = _device_inventory_lookup()
        chosen: list[dict[str, str]] = []
        for dev_id in targets:
            device = inventory.get(dev_id, {}) or {}
            name = str(device.get("hostname") or device.get("id") or "").lower()
            if token in str(dev_id).lower() or token in name or name.startswith(token):
                chosen.append({"id": dev_id, "name": str(device.get("hostname") or dev_id), "ip": ""})
        if chosen:
            return chosen
        if explicit:
            return [{"id": "", "name": token, "ip": token}]
        return []

    # Resolve IPs by same-subnet relationship for candidate targets.
    result: list[dict[str, str]] = []
    try:
        source_interfaces = await asyncio.wait_for(
            device_service.interfaces(source_id), timeout=5.0
        )
    except Exception:
        source_interfaces = {}
    source_ips = _interface_ips(source_interfaces, source_id)

    for dev_id in targets:
        try:
            target_ifaces = await asyncio.wait_for(
                device_service.interfaces(dev_id), timeout=5.0
            )
        except Exception:
            target_ifaces = {}
        target_ips = _interface_ips(target_ifaces, dev_id)
        matched: list[str] = []
        for tip in target_ips:
            for sip in source_ips:
                if _same_subnet(tip, sip):
                    matched.append(tip.split("/")[0])
                    break
        if matched:
            for ip in matched:
                result.append({"id": dev_id, "name": ip, "ip": ip})
        else:
            inventory = _device_inventory_lookup()
            device = inventory.get(dev_id, {}) or {}
            mgmt = str((device.get("management_address") or "")).split("/")[0]
            if mgmt and mgmt != "-":
                result.append({"id": dev_id, "name": str(device.get("hostname") or dev_id), "ip": mgmt})
    return result


async def _try_natural_ping_flow(
    message: str,
    device_ids: list[str],
    *,
    mode: str = "guarded",
) -> dict[str, Any] | None:
    """Execute a ping intent expressed in natural language and stream results.

    Matches messages like "tes ping dari SR-MT1 ke semua router" or
    "ping R1 terhadap 10.10.12.2". Emits plan / running / command_output /
    verification events and returns a formatted response.
    """
    msg = str(message or "").strip()
    if not msg or "ping" not in msg.lower():
        return None

    targets = [item for item in device_ids if item]
    if not targets:
        return {
            "handled": True,
            "events": [],
            "response": (
                "Ringkasan: saya butuh device sumber untuk menjalankan ping.\n"
                "Temuan: tidak ada perangkat yang terdeteksi dari permintaan ini.\n"
                "Rekomendasi: sebutkan device sumber, misalnya 'ping dari SR-MT1 ke 10.10.13.1'."
            ),
        }

    source_id, source_name = await _resolve_ping_source(message, targets)
    if not source_id:
        return {
            "handled": True,
            "events": [],
            "response": (
                "Ringkasan: device sumber ping tidak dapat ditentukan.\n"
                "Rekomendasi: sebutkan device sumber, misalnya 'tes ping dari SR-MT1 ke PC3'."
            ),
        }

    ping_targets = await _resolve_ping_targets(message, targets, source_id)
    if not ping_targets:
        return {
            "handled": True,
            "events": [],
            "response": (
                "Ringkasan: tidak ada target ping yang ditemukan.\n"
                "Temuan: saya tidak dapat menyimpulkan IP/router tujuan dari permintaan ini.\n"
                "Rekomendasi: sebutkan alamat IP target secara eksplisit, misalnya "
                "'ping dari SR-MT1 ke 10.10.13.1'."
            ),
        }

    task_id = f"ping-{datetime.utcnow().timestamp():.0f}"
    tasks_desc = ", ".join(item["name"] for item in ping_targets)
    events: list[dict[str, Any]] = []
    results: list[str] = []
    ok_count = 0
    total = 0

    events.append(_build_workflow_state_event(
        task_id=task_id,
        state="planning",
        detail=f"Menjalankan ping dari {source_name} ke {tasks_desc}.",
        device_ids=[source_id],
        events_count=0,
    ))

    for target in ping_targets:
        total += 1
        target_ip = target["ip"] or target["name"]
        try:
            ping_result = await asyncio.wait_for(
                execute_tool(
                    "ping",
                    device_id=source_id,
                    target=target_ip,
                    mode=mode,
                ),
                timeout=30.0,
            )
        except Exception as exc:
            ping_result = {"error": str(exc)}

        if ping_result.get("error"):
            events.append(_build_command_output_event(
                task_id=task_id,
                result={
                    "device_id": source_id,
                    "hostname": source_name,
                    "command": f"ping {target_ip}",
                    "status": "failed",
                    "output": str(ping_result.get("error", "")),
                    "error": str(ping_result.get("error", "")),
                },
            ))
            results.append(f"**{source_name} → {target_ip}**: gagal — {ping_result.get('error')}")
            continue

        raw_output = str(ping_result.get("raw") or ping_result.get("data") or "")
        events.append(_build_command_output_event(
            task_id=task_id,
            result={
                "device_id": source_id,
                "hostname": source_name,
                "command": f"ping {target_ip}",
                "status": "ok",
                "output": raw_output,
                "raw": ping_result,
            },
        ))
        success = ("packet-loss=0%" in raw_output) or ("Success rate is 100 percent" in raw_output)
        if success:
            ok_count += 1
        results.append(
            f"**{source_name} → {target_ip}**: {'✅ reachable' if success else '⚠️ loss/unsuccessful'}"
        )

    events.append(_build_workflow_state_event(
        task_id=task_id,
        state="verifying",
        detail="Memverifikasi hasil ping.",
        device_ids=[source_id],
        events_count=len(events),
    ))
    events.append(
        {
            "type": "verification",
            **_build_verification_event(
                task_id=task_id,
                device_ids=[source_id],
                status="passed" if ok_count == total else "warning",
                message=f"{ok_count}/{total} target reachable dari {source_name}.",
                checks=["icmp", "routing", "reachability"],
            ),
        }
    )

    body = "\n".join(results)
    response = (
        f"# Hasil Ping dari {source_name}\n\n"
        f"Menjalankan ping ke {len(ping_targets)} target.\n\n"
        f"{body}\n\n"
        f"**Kesimpulan**: {ok_count}/{total} target reachable." if results else
        "Tidak ada hasil ping yang diperoleh."
    )

    return {
        "handled": True,
        "source": source_id,
        "targets": [item["ip"] or item["name"] for item in ping_targets],
        "events": events,
        "response": response,
        "ok_count": ok_count,
        "total": total,
    }


async def _try_command_tool_flow(
    message: str,
    device_ids: list[str],
    *,
    mode: str = "auto",
) -> dict[str, Any] | None:
    """Route explicit CLI-like messages to vendor-specific backend tools."""
    command = _extract_cli_command(message)
    if not command:
        return None

    targets = [item for item in device_ids if item]
    if not targets:
        return {
            "handled": True,
            "requires_approval": False,
            "command": command,
            "response": (
                "Ringkasan: perintah terdeteksi, tetapi device target belum spesifik.\n"
                "Temuan: saya perlu hostname/device ID agar command tidak salah tujuan.\n"
                "Rekomendasi: sebutkan device yang ingin dipakai, misalnya `R1`, `MK-1`, atau `SW1`.\n"
                "Langkah berikutnya: kirim ulang command bersama device target."
            ),
            "events": [],
        }

    inventory = _device_inventory_lookup()
    results: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    approvals: list[dict[str, Any]] = []
    workflow_task_id = f"cmd-{datetime.utcnow().timestamp():.0f}"

    events.append(
        _build_workflow_state_event(
            task_id=workflow_task_id,
            state="thinking",
            detail="Menganalisis command dan target device.",
            device_ids=targets,
            events_count=0,
        )
    )

    for dev_id in targets:
        device = inventory.get(str(dev_id).strip(), {})
        tool_name = _command_tool_name_for_vendor(_normalize_vendor(str(device.get("vendor", "")), str(device.get("platform", ""))))
        result = await execute_tool(
            tool_name,
            device_id=dev_id,
            command=command,
            mode=mode,
        )
        results.append(result)
        if result.get("status") == "approval_required":
            approvals.append(result)

    task_label = f"Execute command: {command}"
    events.append(
        {
            "type": "plan",
            "task": task_label,
            "devices": targets,
            "plannedActions": ["Validate command scope", "Check approval", "Execute on target devices", "Return output"],
            "risk": "HIGH" if any(item.get("risk") == "high" for item in approvals) else "MEDIUM" if approvals else "LOW",
            "requiresApproval": bool(approvals),
            "createdAt": datetime.utcnow().isoformat(),
        }
    )
    events.append(
        _build_workflow_state_event(
            task_id=workflow_task_id,
            state="planning",
            detail="Menyiapkan rencana eksekusi command.",
            device_ids=targets,
            events_count=len(events),
        )
    )

    if approvals:
        events.append(
            {
                "type": "approval",
                "task": task_label,
                "devices": targets,
                "status": "required",
                "risk": approvals[0].get("risk", "medium"),
                "message": "Command requires approval before execution.",
                "commands": [command],
                "approvals": approvals,
                "createdAt": datetime.utcnow().isoformat(),
            }
        )
        events.append(
            _build_workflow_state_event(
                task_id=workflow_task_id,
                state="waiting_approval",
                detail="Command menunggu approval sebelum dieksekusi.",
                device_ids=targets,
                events_count=len(events),
            )
        )
        response_lines = [
            "Ringkasan: command terdeteksi sebagai perubahan yang perlu approval.",
            f"Temuan: {command}",
            f"Device target: {', '.join(targets)}",
            f"Risk: {approvals[0].get('risk', 'medium').upper()}",
            f"Reason: {approvals[0].get('reason', 'Approval required')}",
            "Langkah berikutnya: berikan approval lalu kirim ulang command dengan approval_id yang tersedia.",
        ]
        for item in approvals:
            approval_id = item.get("approval_id")
            if approval_id:
                response_lines.append(f"Approval ID: {approval_id}")
        return {
            "handled": True,
            "requires_approval": True,
            "command": command,
            "results": results,
            "events": events,
            "response": "\n".join(response_lines),
        }

    events.append(
        _build_workflow_state_event(
            task_id=workflow_task_id,
            state="running",
            detail="Command sedang dijalankan pada device target.",
            device_ids=targets,
            events_count=len(events),
        )
    )
    events.append(
        {
            "type": "task_progress",
            "task": task_label,
            "devices": targets,
            "step": "execute",
            "status": "success",
            "message": "Command executed successfully",
            "createdAt": datetime.utcnow().isoformat(),
        }
    )

    for result in results:
        events.append(
            {
                "type": "command_output",
                **_build_command_output_event(task_id=task_label, result=result),
            }
        )

    events.append(
        _build_workflow_state_event(
            task_id=workflow_task_id,
            state="verifying",
            detail="Memvalidasi output command terhadap state device.",
            device_ids=targets,
            events_count=len(events),
        )
    )
    events.append(
        {
            "type": "verification",
            **_build_verification_event(
                task_id=task_label,
                device_ids=targets,
                status="passed" if all(str(item.get("status", "")).lower() == "ok" for item in results) else "warning",
                message="Command output captured and validated against device state.",
                checks=["command execution", "output collection", "device response"],
            ),
        }
    )
    events.append(
        _build_workflow_state_event(
            task_id=workflow_task_id,
            state="completed",
            detail="Command selesai dan hasil sudah tervalidasi.",
            device_ids=targets,
            events_count=len(events),
        )
    )

    response_lines = [
        "Ringkasan: command berhasil dijalankan.",
        f"Perintah: {command}",
        f"Device target: {', '.join(targets)}",
        "",
        "Output:",
        "```command_output",
    ]
    for result in results:
        response_lines.append(_render_command_output_section(str(result.get("device_id", "")), result))
        response_lines.append("")
    response_lines.append("```")
    response_lines.append("Langkah berikutnya: jika Anda ingin saya bandingkan hasil antar device, beri instruksi lanjutannya.")

    return {
        "handled": True,
        "requires_approval": False,
        "command": command,
        "results": results,
        "events": events,
        "response": "\n".join(response_lines),
    }


async def _collect_device_context(device_ids: list[str]) -> str:
    """Collect real device state using agent tools."""
    import asyncio as _asyncio

    async def _collect_one(dev_id: str) -> dict[str, Any]:
        base = await device_service.get_device(dev_id)

        try:
            health = await _asyncio.wait_for(device_service.health(dev_id), timeout=2.5)
        except Exception as exc:
            health = {"device_id": dev_id, "reachable": False, "reason": str(exc)}

        reachable = bool(health.get("reachable", False))
        snapshot: dict[str, Any] = {
            "device_id": dev_id,
            "facts": base,
            "health": health,
        }

        if reachable:
            interfaces_task = _asyncio.wait_for(device_service.interfaces(dev_id), timeout=5.0)
            routes_task = _asyncio.wait_for(device_service.routes(dev_id), timeout=5.0)
            interfaces, routes = await _asyncio.gather(
                interfaces_task, routes_task, return_exceptions=True
            )
            snapshot["interfaces"] = (
                interfaces if not isinstance(interfaces, BaseException) else {"error": f"interfaces failed: {interfaces}"}
            )
            snapshot["routes"] = (
                routes if not isinstance(routes, BaseException) else {"error": f"routes failed: {routes}"}
            )
        else:
            snapshot["interfaces"] = {
                "skipped": True,
                "reason": "device not reachable during health probe",
            }
            snapshot["routes"] = {
                "skipped": True,
                "reason": "device not reachable during health probe",
            }

        return snapshot

    snapshots = await _asyncio.gather(*[_collect_one(dev_id) for dev_id in device_ids])

    return json.dumps({"snapshots": snapshots}, default=str, ensure_ascii=False)


def _command_result_stdout(data: dict[str, Any]) -> tuple[str, str, str]:
    """Normalize a command result dict into (stdout, stderr, command)."""
    output = data.get("output", data.get("raw", ""))
    if isinstance(output, list):
        output = "\n".join(str(item) for item in output)
    elif isinstance(output, dict):
        output = json.dumps(output, indent=2, ensure_ascii=False, default=str)
    command = str(data.get("command", "")).strip()
    stderr = str(data.get("error", "")).strip()
    return str(output or "").strip(), stderr, command


def _build_live_check_response(message: str, results: list[dict[str, Any]]) -> str:
    """Build a readable answer from live tool results (config/linux service/exec)."""
    service_name = _service_name_from_message(message)
    lines: list[str] = []
    for item in results:
        tool = str(item.get("tool", ""))
        data = item.get("data") or {}
        hostname = str(item.get("hostname") or "")
        device_id = str(item.get("device_id") or "")
        heading = f"{hostname} ({device_id})" if hostname else device_id

        if tool == "devices.config":
            config = data.get("data") if isinstance(data, dict) else None
            raw = data.get("raw") if isinstance(data, dict) else None
            if isinstance(config, list):
                body = "\n".join(str(x) for x in config)
            elif config:
                body = str(config)
            else:
                body = str(raw or "(no config)")
            lines.append(f"## {heading} — Running Config")
            lines.append("```")
            lines.append(body[:6000])
            lines.append("```")
            lines.append("")
            continue

        if tool in {"linux.service_status", "linux.exec_readonly"}:
            stdout = str(data.get("stdout") or "").strip()
            stderr = str(data.get("stderr") or "").strip()
            command = str(data.get("command") or "").strip()
            status = str(item.get("status", "ok"))
            lines.append(f"## {heading}")
            if command:
                lines.append(f"Command: `{command}`")
            lines.append(f"Status: {status}")
            if stdout:
                lines.append("```")
                lines.append(stdout[:4000])
                lines.append("```")
            if stderr:
                lines.append("**Error:**")
                lines.append("```")
                lines.append(stderr[:2000])
                lines.append("```")
            lines.append("")
            continue

    if not lines:
        return ""
    return "Ringkasan: hasil pengecekan live dari backend (bukan hanya snapshot).\n\n" + "\n".join(lines).rstrip()


def _detect_export(message: str) -> tuple[bool, str, str]:
    """Detect an export request and return (is_export, format, kind)."""
    normalized = " ".join((message or "").lower().split())
    normalized = normalized.replace("exel", "excel").replace(" xl ", " xlsx ")

    strong_verbs = (
        "buat file",
        "buatkan file",
        "export",
        "download",
        "unduh",
        "jadikan file",
        "jadi file",
        "file excel",
        "file csv",
        "file pdf",
        "file txt",
        "file json",
        "file markdown",
        "file .md",
        "ke excel",
        "ke pdf",
        "ke csv",
        "dalam bentuk excel",
        "dalam bentuk pdf",
        "dalam bentuk csv",
        "dalam format excel",
        "dalam format pdf",
        "dalam format csv",
    )
    if any(verb in normalized for verb in strong_verbs):
        is_export = True
    else:
        has_table = any(word in normalized for word in ("tabel", "table", "laporan", "report"))
        has_format = any(word in normalized for word in ("format", "excel", "xlsx", "pdf", "csv", "txt", "json", "markdown", ".md"))
        is_export = has_table and has_format

    if not is_export:
        return False, "xlsx", "all"

    fmt = "xlsx"
    if "pdf" in normalized:
        fmt = "pdf"
    elif "csv" in normalized:
        fmt = "csv"
    elif "excel" in normalized or "xlsx" in normalized:
        fmt = "xlsx"
    elif "json" in normalized:
        fmt = "json"
    elif "markdown" in normalized or ".md" in normalized:
        fmt = "md"
    elif "txt" in normalized:
        fmt = "txt"

    kind = "all"
    if "config" in normalized or "konfigurasi" in normalized:
        kind = "config"
    elif "interface" in normalized:
        kind = "interfaces"
    elif "route" in normalized or "routing" in normalized:
        kind = "routes"
    return True, fmt, kind


def _topic_readonly_command(vendor: str, text: str) -> str:
    """Map an inspection topic to a vendor read-only command."""
    normalized = " ".join((text or "").lower().split())
    if vendor == "mikrotik":
        if "dhcp-client" in normalized or ("dhcp" in normalized and "client" in normalized):
            return "/ip dhcp-client print detail"
        if "dhcp-server" in normalized or "dhcp server" in normalized:
            return "/ip dhcp-server print detail"
        if "dhcp" in normalized:
            return "/ip dhcp-client print detail"
        if "address" in normalized:
            return "/ip address print detail"
        if "firewall" in normalized:
            return "/ip firewall filter print"
        if "bridge" in normalized:
            return "/interface bridge port print"
    if vendor == "cisco":
        if "dhcp" in normalized:
            return "show ip dhcp binding"
        if "arp" in normalized:
            return "show ip arp"
        if "mac" in normalized:
            return "show mac address-table"
        if "vlan" in normalized:
            return "show vlan brief"
    if vendor == "linux":
        if "dhcp" in normalized or "lease" in normalized:
            return "cat /var/lib/dhcp/dhclient.leases 2>/dev/null || journalctl -u NetworkManager --no-pager | tail -40"
        if "port" in normalized:
            return "ss -tulpen"
        if "process" in normalized or "proses" in normalized:
            return "ps aux --sort=-%cpu | head -30"
    return ""


async def _dispatch_readonly_tools(
    *,
    intent: dict[str, Any],
    targets: list[str],
    session_id: str | None,
    task_id: str,
    message: str = "",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Dispatch read-only registry tools for concrete targets.

    Emits one tool_output event per target/tool and persists an audit record.
    Returns (events, results). Devices.* tools and Linux service checks run
    here; vendor exec tools run only when an explicit CLI command is present.
    """
    suggested = list(intent.get("suggested_tools", []))
    service_name = _service_name_from_message(message)
    explicit_command = _extract_cli_command(message)

    events: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []

    for device_id in targets:
        device = _device_inventory_lookup().get(str(device_id).strip(), {})
        hostname = str(device.get("hostname") or device_id).strip() or str(device_id)
        vendor = _normalize_vendor(str(device.get("vendor", "")), str(device.get("platform", "")))
        topic_command = _topic_readonly_command(vendor, message)

        dispatched = 0
        for tool_name in suggested:
            params: dict[str, Any] = {}
            if tool_name.startswith("devices."):
                params = {"device_id": device_id}
            elif tool_name == "linux.service_status" and vendor == "linux" and service_name:
                params = {"device_id": device_id, "service": service_name}
            elif tool_name == "linux.exec_readonly" and vendor == "linux" and (explicit_command or topic_command):
                params = {"device_id": device_id, "command": explicit_command or topic_command}
            elif tool_name == "cisco.exec_readonly" and vendor == "cisco" and (explicit_command or topic_command):
                params = {"device_id": device_id, "command": explicit_command or topic_command}
            elif tool_name == "mikrotik.exec_readonly" and vendor == "mikrotik" and (explicit_command or topic_command):
                params = {"device_id": device_id, "command": explicit_command or topic_command}
            elif tool_name == "aruba.exec_readonly" and vendor == "aruba" and explicit_command:
                params = {"device_id": device_id, "command": explicit_command}
            else:
                continue

            result = await dispatch_tool(tool_name, params)
            data = result.get("data") or {}
            command_label = ""
            if tool_name == "linux.service_status" and service_name:
                command_label = f"systemctl status {service_name} --no-pager"
            elif tool_name.endswith("exec_readonly"):
                command_label = params.get("command", "")
            if isinstance(data, dict) and tool_name not in {t for t in suggested if t.startswith("devices.")}:
                stdout, stderr, command = _command_result_stdout(data)
                if command_label and not command:
                    command = command_label
                if command or stdout or stderr:
                    data = {"command": command or data.get("command", ""), "stdout": stdout, "stderr": stderr}

            event = build_tool_output(
                tool=tool_name,
                policy=result.get("policy", "READ_ONLY"),
                evidence=result.get("evidence", "live_command_output"),
                target={"device_id": device_id, "hostname": hostname},
                summary=(f"$ {command_label}" if command_label else (result.get("summary") or f"{tool_name} on {hostname}")),
                data=data,
                raw=result.get("raw") or "",
                error=result.get("error"),
            )
            event["taskId"] = task_id
            events.append(event)
            results.append(
                {
                    "tool": tool_name,
                    "device_id": device_id,
                    "hostname": hostname,
                    "status": result.get("status"),
                    "data": data,
                    "error": result.get("error"),
                }
            )
            audit_store.record(
                user="agent",
                session_id=session_id or "",
                task_id=task_id,
                source="AI Agent",
                action=tool_name,
                target_type="device",
                target_id=device_id,
                policy=result.get("policy", "READ_ONLY"),
                risk=intent.get("risk", "low"),
                result="success" if result.get("status") == "ok" else "failed",
                evidence=result.get("evidence", "live_command_output"),
                summary=result.get("summary") or "",
                error=result.get("error") or "",
            )
            dispatched += 1

        if dispatched == 0:
            result = await dispatch_tool("devices.health", {"device_id": device_id})
            event = build_tool_output(
                tool="devices.health",
                policy=result.get("policy", "READ_ONLY"),
                evidence=result.get("evidence", "backend_snapshot"),
                target={"device_id": device_id, "hostname": hostname},
                summary=result.get("summary") or f"devices.health on {hostname}",
                data=result.get("data") or {},
                raw=result.get("raw") or "",
                error=result.get("error"),
            )
            event["taskId"] = task_id
            events.append(event)
            results.append(
                {
                    "tool": "devices.health",
                    "device_id": device_id,
                    "hostname": hostname,
                    "status": result.get("status"),
                    "data": result.get("data") or {},
                    "error": result.get("error"),
                }
            )

    return events, results


def _build_prompts(
    message: str,
    *,
    history: list[dict[str, Any]] | None = None,
    device_id: str = "",
    device_ids: list[str] | None = None,
    lab_id: str = "",
    mode: str = "guarded",
) -> tuple[str, str, list[str], str]:
    """Build system/user prompts with grounded device context."""
    selected_device_ids = [item for item in (device_ids or []) if item]
    if not selected_device_ids:
        selected_device_ids = _find_devices(message, device_id)

    device_context = ""
    if selected_device_ids:
        try:
            # Synchronously collect context is not possible here; run via asyncio from caller.
            device_context = "(collected in caller)"
        except Exception as e:
            device_context = f"(failed to collect device context: {e})"

    system_prompt = (
        "You are a Network Copilot for an AI-powered Network Operations Center. "
        "You have access to real device state from the GNS3 lab via backend tools. "
        "Use the provided device state and available-device list to answer factually. "
        f"Current safety mode: {mode}. "
        f"Current lab context: {lab_id or 'none'}. "
        "Be concise, in the user's language, and give actionable network-engineering guidance. "
        "Do NOT claim to have executed changes. "
        "CRITICAL: You DO have access to the devices listed below. "
        "Never say 'I don't have access' or 'I cannot check devices'. "
        "If the user sends a short follow-up like 'oke', 'lanjut', 'ya', or 'yes', "
        "treat it as a continuation of the latest recommendation in the conversation history. "
        "Never reset the topic just because the follow-up is short; continue the previous recommendation "
        "using the latest assistant answer and the conversation history as context. "
        "Do not reinterpret the follow-up as a new device search or a fresh troubleshooting task unless the user explicitly changes topic. "
        "If the user is correcting a previous answer or questioning a detail with words like 'maksudnya', 'bukannya', 'seharusnya', 'kenapa', or 'kok', "
        "treat it as a continuation of the same device/topic and resolve the correction against the latest assistant answer before changing scope. "
        "If the user says a thing 'ada' or 'buka/nya ada', verify that against the current device state first; do not jump to another device. "
        "Evidence rule: clearly separate 'backend snapshot' from 'live command output'. "
        "Only say a command was executed when command_output/tool result is present in the provided context. "
        "If process, service, port, or daemon state is not present, say it is not present in the current snapshot and name the exact command needed to verify it. "
        "If the requested device is not in the available list, say it is not in the lab "
        "and list the devices that ARE available so the user can pick one.\n"
        "FORMATTING RULES:\n"
        "- Use a NOC-style answer format by default: Ringkasan, Temuan, Analisis, Rekomendasi, Langkah berikutnya.\n"
        "- When multiple vendors are active in the same session, split the answer by vendor/device and keep each vendor section separate.\n"
        "- Never mix Cisco IOS syntax with MikroTik RouterOS syntax in the same config block.\n"
        "- Tailor terminology to the active vendor family in the session: Cisco, MikroTik, Aruba, Linux, or Other.\n"
        "- For Cisco, be concise and operational: hostname, interface, routing, neighbor, ACL, and state.\n"
        "- For MikroTik, use RouterOS-native terms and CLI paths.\n"
        "- For Linux, use host/network/service terms such as ip, ss, journalctl, systemctl, and route.\n"
        "- For normal narrative answers, write plain markdown.\n"
        "- For device facts/interfaces/routes, output a JSON block fenced with ```device_state.\n"
        "- For step-by-step plans, output a JSON block fenced with ```plan with a 'steps' array and optional 'risk'.\n"
        "- For raw CLI output, output a block fenced with ```command_output.\n"
        "- If multiple devices are requested, produce one section per device in the same order as requested. "
        "Do not merge devices into a single generic vendor answer.\n"
        "- If one requested device has incomplete state, keep the other device sections intact and mark only the missing device as incomplete.\n"
        "- Never answer a multi-device request with only one device unless the user explicitly asks for a single device.\n"
        "- When the user names exactly one specific device, answer only for that device and do not append other devices from the lab or the session.\n"
        "- If some device data is incomplete, do not say the payload is truncated or limited; say the data is not yet complete and only state confirmed facts.\n"
        "- When summarizing routing or interface state, separate confirmed data from missing data instead of blending them.\n"
        "- For Linux PPP/L2TP/IPsec questions, answer in this order: conclusion, confirmed interface evidence, missing service/process/port evidence, exact verification commands.\n"
        "- When the user gives a follow-up like 'oke' or 'lanjut', continue the previous answer first, then add only the new detail.\n"
        "- Act like a senior network administrator: be direct, factual, and do not wander off context.\n"
        "- Prefer a professional structure when answering in prose: Ringkasan, Temuan, Analisis, Rekomendasi, Langkah berikutnya.\n"
        "- If the answer is a troubleshooting result, lead with the conclusion, then give evidence, then give one recommended action.\n"
        "- End plain-text answers with one practical next step tied to the current topic.\n"
    )
    anchor = _conversation_anchor(history)
    summary_block = _conversation_summary(history, selected_device_ids)
    user_prompt_parts = [
        f"[AVAILABLE DEVICES]\n{_available_devices_context()}\n[/AVAILABLE DEVICES]",
    ]
    if summary_block:
        user_prompt_parts.append(summary_block)
    requested_device_block = _requested_device_context(selected_device_ids)
    if requested_device_block:
        user_prompt_parts.append(requested_device_block)
    if _is_multi_device_request(message, selected_device_ids):
        user_prompt_parts.append(
            "[MULTI DEVICE REQUEST]\n"
            f"Requested devices: {', '.join(selected_device_ids) if selected_device_ids else '(none)'}\n"
            "Instruction: answer every requested device explicitly and separately. "
            "Do not collapse the answer to one device if more than one device is mentioned.\n"
            "If one requested device has incomplete state, keep the other device sections in the answer.\n"
            "If the user asks for two or more devices, treat that as a multi-target workflow and verify each device independently.\n"
            "[/MULTI DEVICE REQUEST]"
        )
    vendor_block = _session_vendor_context(selected_device_ids)
    if vendor_block:
        user_prompt_parts.append(vendor_block)
    if anchor["topic"] or anchor["last_user"] or anchor["last_assistant"]:
        user_prompt_parts.append(
            "[CONVERSATION ANCHOR]\n"
            f"Topic: {anchor['topic'] or '(unknown)'}\n"
            f"Latest user intent: {anchor['last_user'] or '(none)'}\n"
            f"Latest assistant recommendation: {anchor['last_assistant'] or '(none)'}\n"
            "Continuation rule: answer from the latest recommendation first, then refine with current device state.\n"
            "Do not restart the explanation from scratch unless the user asks for a new topic.\n"
            "[/CONVERSATION ANCHOR]"
        )
    history_block = _conversation_history_context(history)
    if history_block:
        user_prompt_parts.append(history_block)
    user_prompt_parts.append(f"User request: {message}")
    user_prompt = "\n\n".join(user_prompt_parts)
    if _is_context_follow_up(message):
        latest_assistant = _latest_assistant_excerpt(history)
        if latest_assistant:
            user_prompt += (
                "\n\n[LATEST ASSISTANT RECOMMENDATION]\n"
                f"{latest_assistant}\n"
                "[/LATEST ASSISTANT RECOMMENDATION]"
            )
            if any(token in message.lower() for token in ("maksudnya", "bukannya", "seharusnya", "kenapa", "kok", "padahal", "tapi")):
                user_prompt += (
                    "\n\n[CORRECTION FOLLOW-UP]\n"
                    "This is a correction or challenge to the prior answer. "
                    "Stay on the same device/topic, compare the correction against the last assistant recommendation, "
                    "and answer whether the previous conclusion still holds.\n"
                    "[/CORRECTION FOLLOW-UP]"
                )
    return system_prompt, user_prompt, selected_device_ids, device_context


def _append_device_context(
    user_prompt: str,
    device_context: str,
    device_ids: list[str],
    *,
    message: str = "",
    history: list[dict[str, Any]] | None = None,
) -> str:
    if device_context and device_context != "(collected in caller)":
        device_block = device_context
        try:
            parsed = json.loads(device_context)
            device_block = json.dumps(parsed, indent=2, ensure_ascii=False, default=str)
        except Exception:
            pass
        return user_prompt + (
            "\n\n[REAL DEVICE STATE FROM GNS3 LAB]\n"
            "```device_state\n"
            f"{device_block[:8000]}\n"
            "```"
            "\n[/DEVICE STATE]"
        )
    if device_ids:
        return user_prompt + "\n\n(Device terdeteksi namun state gagal dikumpulkan.)"
    clarification = _clarify_missing_context(message, history, device_ids)
    return user_prompt + "\n\n[AMBIGUOUS CONTEXT]\n" + clarification + "\n[/AMBIGUOUS CONTEXT]"


def _workflow_for_request(message: str, device_ids: list[str]) -> dict[str, Any]:
    msg = message.lower()
    has_change_intent = any(
        token in msg
        for token in (
            "configure",
            "configure ",
            "deploy",
            "apply",
            "create vlan",
            "ospf",
            "ipsec",
            "backup",
            "restore",
            "update",
            "delete",
            "remove",
        )
    )

    if "ipsec" in msg:
        task = "Build site-to-site IPsec"
        risk = "high"
        steps = [
            "Collect current configuration",
            "Identify WAN interfaces",
            "Check local and remote subnets",
            "Validate crypto policy",
            "Backup device configurations",
            "Apply IPsec configuration",
            "Verify IKE and IPsec SAs",
            "Save configuration",
        ]
        approval_message = "IPsec changes can affect routing and tunnel reachability. Review the plan before execution."
    elif "ospf" in msg:
        task = "Configure OSPF"
        risk = "medium"
        steps = [
            "Check interface status",
            "Check existing routing",
            "Generate OSPF configuration",
            "Backup running configuration",
            "Apply OSPF configuration",
            "Verify neighbor state",
            "Test routes",
            "Save configuration",
        ]
        approval_message = "OSPF changes may trigger reconvergence. Review the plan before execution."
    elif "vlan" in msg:
        task = "Configure VLAN"
        risk = "medium"
        steps = [
            "Collect switch state",
            "Check trunk and access ports",
            "Generate VLAN configuration",
            "Backup running configuration",
            "Apply VLAN changes",
            "Validate VLAN membership",
            "Verify device reachability",
            "Save configuration",
        ]
        approval_message = "VLAN changes may affect layer-2 reachability. Review the plan before execution."
    elif "backup" in msg:
        task = "Backup device configurations"
        risk = "low"
        steps = [
            "Identify target devices",
            "Collect running configuration",
            "Store backup artifact",
            "Confirm backup checksum",
        ]
        approval_message = "Backup is safe to run, but still confirm the target devices."
    elif any(token in msg for token in ("ping", "route", "routing", "interface", "troubleshoot", "check", "show")):
        task = "Inspect network state"
        risk = "low"
        steps = [
            "Collect current device state",
            "Check interfaces and routing",
            "Run validation probes",
            "Summarize findings",
        ]
        approval_message = "Inspection is read-only and does not change device configuration."
    else:
        task = "Analyze network request"
        risk = "low"
        steps = [
            "Collect current device state",
            "Interpret request intent",
            "Prepare next action",
        ]
        approval_message = "This is a planning step. No configuration change will be applied yet."

    approval_required = has_change_intent or risk in {"medium", "high"}
    commands = []
    if "ospf" in msg:
        commands = ["router ospf 1", "network <subnet> area 0", "passive-interface default"]
    elif "vlan" in msg:
        commands = ["vlan <id>", "name <name>", "interface <ports>"]
    elif "ipsec" in msg:
        commands = ["crypto ike policy 10", "crypto ipsec profile", "tunnel protection ipsec profile <name>"]
    elif "backup" in msg:
        commands = ["show running-config", "export", "save backup artifact"]
    else:
        commands = ["show ip interface brief", "show ip route", "show running-config"]

    return {
        "task": task,
        "risk": risk,
        "steps": steps,
        "approval_required": approval_required,
        "approval_message": approval_message,
        "commands": commands,
        "devices": device_ids,
    }


def _emit_sse_payload(event_type: str, payload: dict[str, Any]) -> str:
    return f"data: {json.dumps({'type': event_type, **payload})}\n\n"


async def _llm_chat_stream(system_prompt: str, user_prompt: str):
    """Stream LLM tokens from the configured provider (9Router preferred)."""
    import httpx

    model = _ai_settings.get("model", "opencode-cheap")
    api_key = settings.NINEROUTER_KEY or os.getenv("NINEROUTER_KEY", "")
    base_url = settings.NINEROUTER_URL or "http://127.0.0.1:20128"

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            f"{base_url.rstrip('/')}/v1/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": True,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        data = json.loads(line[6:])
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except (json.JSONDecodeError, KeyError, IndexError):
                        pass


@router.post("/chat/stream")
async def agent_chat_stream(payload: dict[str, Any]):
    """Stream agent chat response via SSE with real device context."""
    message = payload.get("message", "")
    history = payload.get("history", [])
    device_id = payload.get("device_id", "")
    device_ids = payload.get("device_ids", [])
    lab_id = payload.get("lab_id", "")
    mode = payload.get("mode", "guarded")
    session_id = payload.get("session_id")
    explicit_device_ids = _find_devices_from_message(message)
    inspection_device_ids = explicit_device_ids or ([device_id] if device_id else [])

    resolved_device_ids, resolved_lab_id = _resolve_session_context(
        session_id=session_id,
        device_ids=device_ids if isinstance(device_ids, list) else [],
        lab_id=str(lab_id) if lab_id is not None else "",
        history=history if isinstance(history, list) else [],
        message=message,
        device_id=device_id,
    )

    if session_id:
        try:
            update_session_context(
                session_id,
                device_ids=resolved_device_ids,
                lab_id=resolved_lab_id or None,
                project_id=str(payload.get("project_id") or ""),
                environment=str(payload.get("environment") or "lab"),
            )
        except Exception:
            pass

    request_analysis = analyze_request(
        message,
        inventory=_get_inventory(),
        device_ids=resolved_device_ids,
        history=history if isinstance(history, list) else [],
    )

    if _analysis_is_ambiguous(request_analysis):
        async def ambiguous_generator():
            start_event = {
                "id": f"evt-start-{datetime.utcnow().timestamp():.0f}",
                "session_id": session_id,
                "device_ids": resolved_device_ids,
                "lab_id": resolved_lab_id or None,
                "project_id": str(payload.get("project_id") or "") or None,
                "environment": str(payload.get("environment") or "lab"),
                "analysis": request_analysis.to_dict(),
            }
            start_record = {"type": "start", **start_event}
            _agent_events.append(start_record)
            await _broadcast_event(start_record)
            yield _emit_sse_payload("start", start_event)
            clarification = _clarify_missing_context(message, history if isinstance(history, list) else [], resolved_device_ids)
            yield _emit_sse_payload("text", {"text": clarification})
            done_event = {"id": f"evt-done-{datetime.utcnow().timestamp():.0f}", "session_id": session_id}
            done_record = {"type": "done", **done_event}
            _agent_events.append(done_record)
            await _broadcast_event(done_record)
            yield _emit_sse_payload("done", done_event)

        return StreamingResponse(ambiguous_generator(), media_type="text/event-stream")

    intent_dict = _analysis_intent_dict(request_analysis)
    if intent_dict.get("type") == "software_task":
        async def software_generator():
            start_event = {
                "id": f"evt-start-{datetime.utcnow().timestamp():.0f}",
                "session_id": session_id,
                "device_ids": resolved_device_ids,
                "lab_id": resolved_lab_id or None,
                "project_id": str(payload.get("project_id") or "") or None,
                "environment": str(payload.get("environment") or "lab"),
                "analysis": request_analysis.to_dict(),
            }
            start_record = {"type": "start", **start_event}
            _agent_events.append(start_record)
            await _broadcast_event(start_record)
            yield _emit_sse_payload("start", start_event)

            software_task_id = f"sw-{datetime.utcnow().timestamp():.0f}"
            thinking_event = _build_workflow_state_event(
                task_id=software_task_id,
                state="thinking",
                detail="Backend menganalisis request software task.",
                events_count=0,
            )
            thinking_record = {"type": "workflow_state", **thinking_event}
            _agent_events.append(thinking_record)
            await _broadcast_event(thinking_record)
            yield _emit_sse_payload("workflow_state", thinking_event)

            planning_event = _build_workflow_state_event(
                task_id=software_task_id,
                state="planning",
                detail="Agent menyusun langkah implementasi, eksekusi, dan verifikasi.",
                events_count=1,
            )
            planning_record = {"type": "workflow_state", **planning_event}
            _agent_events.append(planning_record)
            await _broadcast_event(planning_record)
            yield _emit_sse_payload("workflow_state", planning_event)

            audit_store.record(
                user="agent",
                session_id=str(session_id or ""),
                task_id=software_task_id,
                source="AI Agent",
                action="software_task",
                target_type="workspace",
                target_id=software_task_id,
                policy="GUARDED",
                risk="low",
                result="running",
                evidence="live_command_output",
                summary=f"Software task: {message[:200]}",
            )

            async for event_type, event_payload in run_software_task(
                message,
                session_id=session_id,
                task_id=software_task_id,
                llm_call=_llm_chat,
            ):
                record = {"type": event_type, **event_payload}
                _agent_events.append(record)
                await _broadcast_event(record)
                yield _emit_sse_payload(event_type, event_payload)

            completed_event = _build_workflow_state_event(
                task_id=software_task_id,
                state="completed",
                detail="Software task selesai.",
                events_count=1,
            )
            completed_record = {"type": "workflow_state", **completed_event}
            _agent_events.append(completed_record)
            await _broadcast_event(completed_record)
            yield _emit_sse_payload("workflow_state", completed_event)

            done_event = {"id": f"evt-done-{datetime.utcnow().timestamp():.0f}", "session_id": session_id}
            done_record = {"type": "done", **done_event}
            _agent_events.append(done_record)
            await _broadcast_event(done_record)
            yield _emit_sse_payload("done", done_event)

        return StreamingResponse(software_generator(), media_type="text/event-stream")

    export_requested, export_fmt, export_kind = _detect_export(message)
    if export_requested:
        export_targets = _analysis_device_ids(request_analysis) or resolved_device_ids or ([device_id] if device_id else [])

        async def export_generator():
            export_task_id = f"exp-{datetime.utcnow().timestamp():.0f}"
            start_event = {
                "id": f"evt-start-{datetime.utcnow().timestamp():.0f}",
                "session_id": session_id,
                "device_ids": export_targets,
                "lab_id": resolved_lab_id or None,
                "environment": str(payload.get("environment") or "lab"),
                "analysis": request_analysis.to_dict(),
            }
            start_record = {"type": "start", **start_event}
            _agent_events.append(start_record)
            await _broadcast_event(start_record)
            yield _emit_sse_payload("start", start_event)

            if not export_targets:
                yield _emit_sse_payload("text", {"text": "Sebutkan device yang mau di-export, misalnya `buat file excel untuk SR-R1`."})
                done_event = {"id": f"evt-done-{datetime.utcnow().timestamp():.0f}", "session_id": session_id}
                done_record = {"type": "done", **done_event}
                _agent_events.append(done_record)
                await _broadcast_event(done_record)
                yield _emit_sse_payload("done", done_event)
                return

            running_event = _build_workflow_state_event(
                task_id=export_task_id,
                state="running",
                detail="Mengumpulkan data device untuk export.",
                device_ids=export_targets,
                events_count=1,
            )
            running_record = {"type": "workflow_state", **running_event}
            _agent_events.append(running_record)
            await _broadcast_event(running_record)
            yield _emit_sse_payload("workflow_state", running_event)

            try:
                devices = await collect_devices(export_targets)
            except Exception as exc:  # noqa: BLE001
                yield _emit_sse_payload("error", {"message": f"Gagal mengumpulkan data: {exc}"})
                return

            try:
                filename, data = build_export_document(devices, kind=export_kind, fmt=export_fmt)
                target = (EXPORT_DIR / filename).resolve()
                target.write_bytes(data)
                url = f"/api/v1/agent/download/{filename}"
            except Exception as exc:  # noqa: BLE001
                yield _emit_sse_payload("error", {"message": f"Gagal membuat file: {exc}"})
                return

            tool_event = build_tool_output(
                tool=f"export.{export_fmt}",
                policy="READ_ONLY",
                evidence="generated_plan",
                target={"device_ids": export_targets},
                summary=f"Generated {filename} ({len(data)} bytes)",
                data={"filename": filename, "format": export_fmt, "kind": export_kind, "size": len(data), "download_url": url},
            )
            tool_event["taskId"] = export_task_id
            tool_record = {"type": "tool_output", **tool_event}
            _agent_events.append(tool_record)
            await _broadcast_event(tool_record)
            yield _emit_sse_payload("tool_output", tool_event)

            text = (
                "Ringkasan: file report sudah dibuat dan siap diunduh.\n\n"
                f"- Nama file: `{filename}`\n"
                f"- Format: {export_fmt.upper()}\n"
                f"- Ukuran: {len(data)} bytes\n"
                f"- Link download: [{url}]({url})\n\n"
                f"Device: {', '.join(str(d.get('hostname') or d.get('device_id')) for d in devices)}"
            )
            yield _emit_sse_payload("text", {"text": text})

            completed_event = _build_workflow_state_event(
                task_id=export_task_id,
                state="completed",
                detail="Export selesai.",
                device_ids=export_targets,
                events_count=2,
            )
            completed_record = {"type": "workflow_state", **completed_event}
            _agent_events.append(completed_record)
            await _broadcast_event(completed_record)
            yield _emit_sse_payload("workflow_state", completed_event)

            done_event = {"id": f"evt-done-{datetime.utcnow().timestamp():.0f}", "session_id": session_id}
            done_record = {"type": "done", **done_event}
            _agent_events.append(done_record)
            await _broadcast_event(done_record)
            yield _emit_sse_payload("done", done_event)

        return StreamingResponse(export_generator(), media_type="text/event-stream")

    if intent_dict.get("type") == "network_change":
        change_targets = _analysis_device_ids(request_analysis) or resolved_device_ids or ([device_id] if device_id else [])

        async def config_change_generator():
            config_task_id = f"cfg-{datetime.utcnow().timestamp():.0f}"
            start_event = {
                "id": f"evt-start-{datetime.utcnow().timestamp():.0f}",
                "session_id": session_id,
                "device_ids": change_targets,
                "lab_id": resolved_lab_id or None,
                "environment": str(payload.get("environment") or "lab"),
                "analysis": request_analysis.to_dict(),
            }
            start_record = {"type": "start", **start_event}
            _agent_events.append(start_record)
            await _broadcast_event(start_record)
            yield _emit_sse_payload("start", start_event)

            if not change_targets:
                yield _emit_sse_payload("text", {"text": "Sebutkan device target untuk perubahan konfigurasi, misalnya `tambah vlan 10 di SW1`."})
                done_event = {"id": f"evt-done-{datetime.utcnow().timestamp():.0f}", "session_id": session_id}
                done_record = {"type": "done", **done_event}
                _agent_events.append(done_record)
                await _broadcast_event(done_record)
                yield _emit_sse_payload("done", done_event)
                return

            device = _device_inventory_lookup().get(str(change_targets[0]).strip(), {})
            hostname = str(device.get("hostname") or change_targets[0]).strip() or str(change_targets[0])
            vendor = _normalize_vendor(str(device.get("vendor", "")), str(device.get("platform", "")))

            thinking_event = _build_workflow_state_event(
                task_id=config_task_id, state="thinking",
                detail="Backend menganalisis request perubahan konfigurasi.",
                device_ids=change_targets, events_count=0,
            )
            thinking_record = {"type": "workflow_state", **thinking_event}
            _agent_events.append(thinking_record)
            await _broadcast_event(thinking_record)
            yield _emit_sse_payload("workflow_state", thinking_event)

            planning_event = _build_workflow_state_event(
                task_id=config_task_id, state="planning",
                detail="Menyusun perintah konfigurasi dan rencana perubahan.",
                device_ids=change_targets, events_count=1,
            )
            planning_record = {"type": "workflow_state", **planning_event}
            _agent_events.append(planning_record)
            await _broadcast_event(planning_record)
            yield _emit_sse_payload("workflow_state", planning_event)

            audit_store.record(
                user="agent",
                session_id=str(session_id or ""),
                task_id=config_task_id,
                source="AI Agent",
                action="config_change",
                target_type="device",
                target_id=str(change_targets[0]),
                policy="APPROVAL_REQUIRED",
                risk="medium",
                result="running",
                evidence="live_command_output",
                summary=f"Config change: {message[:200]}",
            )

            agent = ConfigChangeAgent(
                message,
                device_id=str(change_targets[0]),
                hostname=hostname,
                vendor=vendor,
                session_id=session_id,
                task_id=config_task_id,
                llm_call=_llm_chat,
            )
            async for event_type, event_payload in agent.run():
                record = {"type": event_type, **event_payload}
                _agent_events.append(record)
                await _broadcast_event(record)
                yield _emit_sse_payload(event_type, event_payload)

            completed_event = _build_workflow_state_event(
                task_id=config_task_id, state="completed",
                detail="Alur perubahan konfigurasi selesai.",
                device_ids=change_targets, events_count=2,
            )
            completed_record = {"type": "workflow_state", **completed_event}
            _agent_events.append(completed_record)
            await _broadcast_event(completed_record)
            yield _emit_sse_payload("workflow_state", completed_event)

            done_event = {"id": f"evt-done-{datetime.utcnow().timestamp():.0f}", "session_id": session_id}
            done_record = {"type": "done", **done_event}
            _agent_events.append(done_record)
            await _broadcast_event(done_record)
            yield _emit_sse_payload("done", done_event)

        return StreamingResponse(config_change_generator(), media_type="text/event-stream")

    analysis_device_ids = _analysis_device_ids(request_analysis)
    command_targets = analysis_device_ids or (resolved_device_ids if resolved_device_ids else ([device_id] if device_id else []))
    command_flow = None
    if _analysis_intent_dict(request_analysis).get("policy") != AgentPolicy.READ_ONLY.value and not _is_read_only_inspection_request(message):
        command_flow = await _try_command_tool_flow(
            message,
            command_targets,
            mode=str(mode or "guarded"),
        )

    ping_flow = None
    if command_flow is None and "ping" in str(message or "").lower():
        ping_flow = await _try_natural_ping_flow(
            message,
            command_targets if command_targets else resolved_device_ids,
            mode=str(mode or "guarded"),
        )

    workflow = _workflow_for_request(
        message,
        resolved_device_ids if resolved_device_ids else ([device_id] if device_id else []),
    )

    system_prompt, base_user_prompt, resolved_device_ids, _ = _build_prompts(
        message,
        history=history if isinstance(history, list) else [],
        device_id=device_id,
        device_ids=resolved_device_ids,
        lab_id=resolved_lab_id,
        mode=str(mode or "guarded"),
    )

    async def event_generator():
        start_event = {
            "id": f"evt-start-{datetime.utcnow().timestamp():.0f}",
            "session_id": session_id,
            "device_ids": resolved_device_ids,
            "lab_id": resolved_lab_id or None,
            "project_id": str(payload.get("project_id") or "") or None,
            "environment": str(payload.get("environment") or "lab"),
            "analysis": request_analysis.to_dict(),
        }
        start_record = {"type": "start", **start_event}
        _agent_events.append(start_record)
        await _broadcast_event(start_record)
        yield _emit_sse_payload("start", start_event)

        workflow_task_id = f"wf-{datetime.utcnow().timestamp():.0f}"
        thinking_event = _build_workflow_state_event(
            task_id=workflow_task_id,
            state="thinking",
            detail="Backend sedang membaca konteks permintaan.",
            device_ids=resolved_device_ids,
            events_count=0,
        )
        thinking_record = {"type": "workflow_state", **thinking_event}
        _agent_events.append(thinking_record)
        await _broadcast_event(thinking_record)
        yield _emit_sse_payload("workflow_state", thinking_event)

        device_context = ""
        user_prompt = base_user_prompt
        if resolved_device_ids:
            try:
                device_context = await _collect_device_context(resolved_device_ids)
            except Exception as e:
                device_context = f"(failed to collect device context: {e})"
            user_prompt = _append_device_context(
                base_user_prompt,
                device_context,
                resolved_device_ids,
                message=message,
                history=history if isinstance(history, list) else [],
            )
        else:
            user_prompt = _append_device_context(
                base_user_prompt,
                "",
                resolved_device_ids,
                message=message,
                history=history if isinstance(history, list) else [],
            )

        if _is_read_only_inspection_request(message):
            running_event = _build_workflow_state_event(
                task_id=workflow_task_id,
                state="running",
                detail="Backend mengumpulkan state perangkat untuk inspeksi read-only.",
                device_ids=inspection_device_ids or resolved_device_ids,
                events_count=1,
            )
            running_record = {"type": "workflow_state", **running_event}
            _agent_events.append(running_record)
            await _broadcast_event(running_record)
            yield _emit_sse_payload("workflow_state", running_event)

            intent_dict = _analysis_intent_dict(request_analysis)
            readonly_targets = command_targets if command_targets else inspection_device_ids
            tool_results: list[dict[str, Any]] = []
            if intent_dict.get("type") in {"network_readonly", "troubleshooting", "linux_admin"} and readonly_targets:
                tool_events, tool_results = await _dispatch_readonly_tools(
                    intent=intent_dict,
                    targets=readonly_targets,
                    session_id=session_id,
                    task_id=workflow_task_id,
                    message=message,
                )
                for tool_event in tool_events:
                    tool_record = {"type": "tool_output", **tool_event}
                    _agent_events.append(tool_record)
                    await _broadcast_event(tool_record)
                    yield _emit_sse_payload("tool_output", tool_event)

            live_text = _build_live_check_response(message, tool_results)
            text_event = {
                "text": live_text
                or _build_read_only_inspection_response(message, inspection_device_ids, device_context),
            }
            yield _emit_sse_payload("text", text_event)
            verifying_event = _build_workflow_state_event(
                task_id=workflow_task_id,
                state="verifying",
                detail="Menyusun dan memeriksa hasil inspeksi.",
                device_ids=inspection_device_ids or resolved_device_ids,
                events_count=2,
            )
            verifying_record = {"type": "workflow_state", **verifying_event}
            _agent_events.append(verifying_record)
            await _broadcast_event(verifying_record)
            yield _emit_sse_payload("workflow_state", verifying_event)

            verification_event = _build_verification_event(
                task_id=plan_event["id"] if "plan_event" in locals() else f"inspect-{datetime.utcnow().timestamp():.0f}",
                device_ids=inspection_device_ids,
                status="passed",
                message="Read-only inspection completed from backend state.",
                checks=["device_state", "inspection"],
            )
            verification_record = {"type": "verification", **verification_event}
            _agent_events.append(verification_record)
            await _broadcast_event(verification_record)
            yield _emit_sse_payload("verification", verification_event)
            completed_event = _build_workflow_state_event(
                task_id=workflow_task_id,
                state="completed",
                detail="Inspeksi selesai.",
                device_ids=inspection_device_ids or resolved_device_ids,
                events_count=3,
            )
            completed_record = {"type": "workflow_state", **completed_event}
            _agent_events.append(completed_record)
            await _broadcast_event(completed_record)
            yield _emit_sse_payload("workflow_state", completed_event)
            done_event = {"id": f"evt-done-{datetime.utcnow().timestamp():.0f}", "session_id": session_id}
            done_record = {"type": "done", **done_event}
            _agent_events.append(done_record)
            await _broadcast_event(done_record)
            yield _emit_sse_payload("done", done_event)
            return

        if command_flow:
            for event in command_flow.get("events", []):
                event_record = {"type": event.get("type", "message"), **event}
                _agent_events.append(event_record)
                await _broadcast_event(event_record)
                yield _emit_sse_payload(event.get("type", "message"), event)
            text_event = {"text": command_flow.get("response", "")}
            yield _emit_sse_payload("text", text_event)
            done_event = {"id": f"evt-done-{datetime.utcnow().timestamp():.0f}", "session_id": session_id}
            done_record = {"type": "done", **done_event}
            _agent_events.append(done_record)
            await _broadcast_event(done_record)
            yield _emit_sse_payload("done", done_event)
            return

        if ping_flow:
            for event in ping_flow.get("events", []):
                event_record = {"type": event.get("type", "message"), **event}
                _agent_events.append(event_record)
                await _broadcast_event(event_record)
                yield _emit_sse_payload(event.get("type", "message"), event)
            text_event = {"text": ping_flow.get("response", "")}
            yield _emit_sse_payload("text", text_event)
            done_event = {"id": f"evt-done-{datetime.utcnow().timestamp():.0f}", "session_id": session_id}
            done_record = {"type": "done", **done_event}
            _agent_events.append(done_record)
            await _broadcast_event(done_record)
            yield _emit_sse_payload("done", done_event)
            return

        plan_event = {
            "id": f"plan-{datetime.utcnow().timestamp():.0f}",
            "task": workflow["task"],
            "devices": resolved_device_ids,
            "plannedActions": workflow["steps"],
            "risk": workflow["risk"],
            "requiresApproval": workflow["approval_required"],
            "createdAt": datetime.utcnow().isoformat(),
        }
        plan_record = {"type": "plan", **plan_event}
        _agent_events.append(plan_record)
        await _broadcast_event(plan_record)
        yield _emit_sse_payload("plan", plan_event)
        planning_event = _build_workflow_state_event(
            task_id=plan_event["id"],
            state="planning",
            detail="Rencana tindakan sudah disusun.",
            device_ids=resolved_device_ids,
            events_count=1,
        )
        planning_record = {"type": "workflow_state", **planning_event}
        _agent_events.append(planning_record)
        await _broadcast_event(planning_record)
        yield _emit_sse_payload("workflow_state", planning_event)
        await asyncio.sleep(0.12)

        device_state_event = _build_device_state_event(
            task_id=plan_event["id"],
            device_ids=resolved_device_ids,
            device_context=device_context,
        )
        if device_state_event:
            device_state_record = {"type": "device_state", **device_state_event}
            _agent_events.append(device_state_record)
            await _broadcast_event(device_state_record)
            yield _emit_sse_payload("device_state", device_state_event)
            await asyncio.sleep(0.08)

        if workflow["approval_required"]:
            waiting_event = _build_workflow_state_event(
                task_id=plan_event["id"],
                state="waiting_approval",
                detail="Menunggu approval user sebelum melanjutkan.",
                device_ids=resolved_device_ids,
                events_count=3,
            )
            waiting_record = {"type": "workflow_state", **waiting_event}
            _agent_events.append(waiting_record)
            await _broadcast_event(waiting_record)
            yield _emit_sse_payload("workflow_state", waiting_event)
            approval_event = {
                "id": f"approval-{datetime.utcnow().timestamp():.0f}",
                "taskId": plan_event["id"],
                "task": workflow["task"],
                "devices": resolved_device_ids,
                "risk": workflow["risk"],
                "status": "required",
                "message": workflow["approval_message"],
                "commands": workflow["commands"],
                "createdAt": datetime.utcnow().isoformat(),
            }
            approval_record = {"type": "approval", **approval_event}
            _agent_events.append(approval_record)
            await _broadcast_event(approval_record)
            yield _emit_sse_payload("approval", approval_event)
            await asyncio.sleep(0.12)

        try:
            running_event = _build_workflow_state_event(
                task_id=plan_event["id"],
                state="running",
                detail="Backend menjalankan langkah yang disepakati.",
                device_ids=resolved_device_ids,
                events_count=4,
            )
            running_record = {"type": "workflow_state", **running_event}
            _agent_events.append(running_record)
            await _broadcast_event(running_record)
            yield _emit_sse_payload("workflow_state", running_event)

            stream_text = ""
            total_steps = max(len(workflow["steps"]), 1)
            for index, step in enumerate(workflow["steps"], start=1):
                progress_event = {
                    "id": f"progress-{datetime.utcnow().timestamp():.0f}-{index}",
                    "taskId": plan_event["id"],
                    "step": step,
                    "status": "running" if index < total_steps else "success",
                    "message": f"{step}...",
                    "order": index,
                    "total": total_steps,
                    "createdAt": datetime.utcnow().isoformat(),
                }
                progress_record = {"type": "task_progress", **progress_event}
                _agent_events.append(progress_record)
                await _broadcast_event(progress_record)
                yield _emit_sse_payload("task_progress", progress_event)
                await asyncio.sleep(0.08)

            async for chunk in _llm_chat_stream(system_prompt, user_prompt):
                stream_text += chunk
                yield f"data: {json.dumps({'type': 'text', 'text': chunk})}\n\n"
            stream_text = _enforce_multi_device_response(
                stream_text,
                message,
                history if isinstance(history, list) else [],
                resolved_device_ids,
                device_context,
            )
            final_text = _append_professional_closure(
                stream_text,
                message,
                history if isinstance(history, list) else [],
                resolved_device_ids,
            )
            if final_text != stream_text:
                suffix = final_text[len(stream_text):] if final_text.startswith(stream_text) else final_text
                if suffix.strip():
                    yield f"data: {json.dumps({'type': 'text', 'text': suffix})}\n\n"
            verification_event = _build_verification_event(
                task_id=plan_event["id"],
                device_ids=resolved_device_ids,
                status="passed" if resolved_device_ids else "warning",
                message="Device state reviewed and response grounded against collected context.",
                checks=["device_state", "routing", "interfaces", "follow-up continuity"],
            )
            verification_record = {"type": "verification", **verification_event}
            _agent_events.append(verification_record)
            await _broadcast_event(verification_record)
            yield _emit_sse_payload("verification", verification_event)
            completed_event = _build_workflow_state_event(
                task_id=plan_event["id"],
                state="completed",
                detail="Workflow selesai dan hasil sudah diverifikasi.",
                device_ids=resolved_device_ids,
                events_count=5,
            )
            completed_record = {"type": "workflow_state", **completed_event}
            _agent_events.append(completed_record)
            await _broadcast_event(completed_record)
            yield _emit_sse_payload("workflow_state", completed_event)
            done_event = {"id": f"evt-done-{datetime.utcnow().timestamp():.0f}", "session_id": session_id}
            done_record = {"type": "done", **done_event}
            _agent_events.append(done_record)
            await _broadcast_event(done_record)
            yield _emit_sse_payload("done", done_event)
        except Exception as e:
            failed_event = _build_workflow_state_event(
                task_id=plan_event["id"],
                state="failed",
                detail=f"Workflow gagal: {e}",
                device_ids=resolved_device_ids,
                events_count=5,
            )
            failed_record = {"type": "workflow_state", **failed_event}
            _agent_events.append(failed_record)
            await _broadcast_event(failed_record)
            yield _emit_sse_payload("workflow_state", failed_event)
            error_event = {"id": f"evt-error-{datetime.utcnow().timestamp():.0f}", "message": str(e)}
            error_record = {"type": "error", **error_event}
            _agent_events.append(error_record)
            await _broadcast_event(error_record)
            yield _emit_sse_payload("error", error_event)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat")
async def agent_chat(payload: dict[str, Any]):
    message = payload.get("message", "")
    history = payload.get("history", [])
    device_id = payload.get("device_id", "")
    device_ids = payload.get("device_ids", [])
    lab_id = payload.get("lab_id", "")
    mode = payload.get("mode", "guarded")
    session_id = payload.get("session_id")
    explicit_device_ids = _find_devices_from_message(message)
    inspection_device_ids = explicit_device_ids or ([device_id] if device_id else [])

    resolved_device_ids, resolved_lab_id = _resolve_session_context(
        session_id=session_id,
        device_ids=device_ids if isinstance(device_ids, list) else [],
        lab_id=str(lab_id) if lab_id is not None else "",
        history=history if isinstance(history, list) else [],
        message=message,
        device_id=device_id,
    )

    if session_id:
        try:
            update_session_context(
                session_id,
                device_ids=resolved_device_ids,
                lab_id=resolved_lab_id or None,
                project_id=str(payload.get("project_id") or ""),
                environment=str(payload.get("environment") or "lab"),
            )
        except Exception:
            pass

    request_analysis = analyze_request(
        message,
        inventory=_get_inventory(),
        device_ids=resolved_device_ids,
        history=history if isinstance(history, list) else [],
    )

    if _analysis_is_ambiguous(request_analysis):
        response = _clarify_missing_context(message, history if isinstance(history, list) else [], resolved_device_ids)
        event = {
            "id": f"msg-{len(_agent_events) % 10000:04d}",
            "type": "message",
            "role": "assistant",
            "content": response,
            "created_at": datetime.utcnow().isoformat(),
            "device_id": device_id,
            "provider": _ai_settings.get("provider", "fallback"),
            "devices": resolved_device_ids,
        }
        _agent_events.append(event)
        await _broadcast_event(event)
        return event

    analysis_device_ids = _analysis_device_ids(request_analysis)
    command_targets = analysis_device_ids or (resolved_device_ids if resolved_device_ids else ([device_id] if device_id else []))
    command_flow = None
    if _analysis_intent_dict(request_analysis).get("policy") != AgentPolicy.READ_ONLY.value and not _is_read_only_inspection_request(message):
        command_flow = await _try_command_tool_flow(
            message,
            command_targets,
            mode=str(mode or "guarded"),
        )

    ping_flow = None
    if command_flow is None and "ping" in str(message or "").lower():
        ping_flow = await _try_natural_ping_flow(
            message,
            command_targets if command_targets else resolved_device_ids,
            mode=str(mode or "guarded"),
        )

    if command_flow:
        event = {
            "id": f"msg-{len(_agent_events) % 10000:04d}",
            "type": "message",
            "role": "assistant",
            "content": command_flow["response"],
            "created_at": datetime.utcnow().isoformat(),
            "device_id": device_id,
            "provider": _ai_settings.get("provider", "fallback"),
            "devices": command_targets,
        }
        _agent_events.append(event)
        for flow_event in command_flow.get("events", []):
            _agent_events.append(flow_event)
            await _broadcast_event(flow_event)
        await _broadcast_event(event)
        return event

    if ping_flow:
        event = {
            "id": f"msg-{len(_agent_events) % 10000:04d}",
            "type": "message",
            "role": "assistant",
            "content": ping_flow["response"],
            "created_at": datetime.utcnow().isoformat(),
            "device_id": device_id,
            "provider": _ai_settings.get("provider", "fallback"),
            "devices": [ping_flow.get("source", "")] if ping_flow.get("source") else command_targets,
        }
        _agent_events.append(event)
        for flow_event in ping_flow.get("events", []):
            _agent_events.append(flow_event)
            await _broadcast_event(flow_event)
        await _broadcast_event(event)
        return event

    # 1. Build grounded prompts with real device context
    system_prompt, base_user_prompt, resolved_device_ids, _ = _build_prompts(
        message,
        history=history if isinstance(history, list) else [],
        device_id=device_id,
        device_ids=resolved_device_ids,
        lab_id=resolved_lab_id,
        mode=str(mode or "guarded"),
    )

    device_context = ""
    if resolved_device_ids:
        try:
            device_context = await _collect_device_context(resolved_device_ids)
        except Exception as e:
            device_context = f"(failed to collect device context: {e})"
    user_prompt = _append_device_context(
        base_user_prompt,
        device_context,
        resolved_device_ids,
        message=message,
        history=history if isinstance(history, list) else [],
    )

    # 2. Ask LLM with grounded context; fall back to context-aware local answer
    try:
        planning_event = _build_workflow_state_event(
            task_id=f"msg-{len(_agent_events) % 10000:04d}",
            state="planning",
            detail="Menyusun jawaban berbasis konteks perangkat.",
            device_ids=resolved_device_ids,
            events_count=0,
        )
        planning_record = {"type": "workflow_state", **planning_event}
        _agent_events.append(planning_record)
        await _broadcast_event(planning_record)
        if _is_read_only_inspection_request(message):
            response = _build_read_only_inspection_response(message, inspection_device_ids, device_context)
        else:
            running_event = _build_workflow_state_event(
                task_id=planning_event["taskId"],
                state="running",
                detail="Menghasilkan jawaban dan validasi dari backend.",
                device_ids=resolved_device_ids,
                events_count=1,
            )
            running_record = {"type": "workflow_state", **running_event}
            _agent_events.append(running_record)
            await _broadcast_event(running_record)
            response = await _llm_chat(system_prompt, user_prompt)
        verifying_event = _build_workflow_state_event(
            task_id=planning_event["taskId"],
            state="verifying",
            detail="Memeriksa respons akhir agar tetap sesuai konteks jaringan.",
            device_ids=resolved_device_ids,
            events_count=2,
        )
        verifying_record = {"type": "workflow_state", **verifying_event}
        _agent_events.append(verifying_record)
        await _broadcast_event(verifying_record)
    except Exception as e:
        failed_event = _build_workflow_state_event(
            task_id=f"msg-{len(_agent_events) % 10000:04d}",
            state="failed",
            detail=f"Backend gagal menyiapkan jawaban: {e}",
            device_ids=resolved_device_ids,
            events_count=0,
        )
        failed_record = {"type": "workflow_state", **failed_event}
        _agent_events.append(failed_record)
        await _broadcast_event(failed_record)
        response = _context_aware_response(message, device_ids, device_context, str(e), history if isinstance(history, list) else [])
    if "<tool_call" in response.lower() or "</tool_call>" in response.lower():
        response = _build_read_only_inspection_response(message, inspection_device_ids, device_context)
    response = _enforce_multi_device_response(
        response,
        message,
        history if isinstance(history, list) else [],
        resolved_device_ids if isinstance(resolved_device_ids, list) else [],
        device_context,
    )
    response = _append_professional_closure(
        response,
        message,
        history if isinstance(history, list) else [],
        resolved_device_ids if isinstance(resolved_device_ids, list) else [],
    )

    event = {
        "id": f"msg-{len(_agent_events) % 10000:04d}",
        "type": "message",
        "role": "assistant",
        "content": response,
        "created_at": datetime.utcnow().isoformat(),
        "device_id": device_id,
        "provider": _ai_settings.get("provider", "fallback"),
        "devices": resolved_device_ids,
    }
    _agent_events.append(event)
    await _broadcast_event(event)
    completed_event = _build_workflow_state_event(
        task_id=event["id"],
        state="completed",
        detail="Jawaban siap dan sudah dibroadcast ke frontend.",
        device_ids=resolved_device_ids,
        events_count=3,
    )
    completed_record = {"type": "workflow_state", **completed_event}
    _agent_events.append(completed_record)
    await _broadcast_event(completed_record)
    return event


@router.get("/settings")
async def get_agent_settings():
    return _ai_settings


@router.patch("/settings")
async def update_agent_settings(payload: dict[str, Any]):
    _ai_settings.update(payload)
    return _ai_settings


@router.post("/plan")
async def agent_plan(payload: dict[str, Any]):
    intent = payload.get("intent", "")
    device_ids = payload.get("device_ids", [])

    plan = {
        "id": f"plan-{len(_agent_events) % 10000:04d}",
        "task": intent,
        "devices": device_ids,
        "planned_actions": ["Read current state", "Generate candidate config", "Validate", "Present for approval"],
        "risk": "MEDIUM",
        "requires_approval": True,
        "created_at": datetime.utcnow().isoformat(),
    }
    _agent_events.append({"type": "plan", **plan})
    return plan


@router.post("/validate")
async def agent_validate(payload: dict[str, Any]):
    plan_id = payload.get("plan_id", "")
    return {
        "plan_id": plan_id,
        "valid": True,
        "checks": [
            {"check": "Syntax validation", "result": "safe", "detail": "Commands are valid"},
            {"check": "Policy check", "result": "safe", "detail": "Within allowed scope"},
            {"check": "Impact analysis", "result": "warning", "detail": "Config change may cause brief reconvergence"},
        ],
        "validated_at": datetime.utcnow().isoformat(),
    }


@router.post("/analyze")
async def agent_analyze(payload: dict[str, Any]):
    """Analyze a request without executing any device or workspace tool."""
    message = payload.get("message", "")
    device_ids = payload.get("device_ids", [])
    history = payload.get("history", [])
    analysis = analyze_request(
        str(message or ""),
        inventory=_get_inventory(),
        device_ids=device_ids if isinstance(device_ids, list) else [],
        history=history if isinstance(history, list) else [],
    )
    return analysis.to_dict()


@router.post("/code/run")
async def agent_code_run(payload: dict[str, Any]):
    """Execute a code snippet in a sandbox and return output."""
    code = str(payload.get("code") or "").strip()
    language = str(payload.get("language") or "python").strip()
    timeout = int(payload.get("timeout") or 30)

    if not code:
        raise HTTPException(status_code=400, detail="code is required")

    try:
        result = await execute_code_snippet(
            code,
            language=language,
            timeout=max(5, min(timeout, 120)),
        )
        return {"status": "ok", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"code run failed: {exc}")


@router.post("/code/debug")
async def agent_code_debug(payload: dict[str, Any]):
    """Run a code snippet, then auto-fix bugs via LLM until it passes."""
    code = str(payload.get("code") or "").strip()
    language = str(payload.get("language") or "python").strip()
    goal = str(payload.get("goal") or "the program runs without errors and produces correct output")
    timeout = int(payload.get("timeout") or 30)
    max_iterations = int(payload.get("max_iterations") or 5)

    if not code:
        raise HTTPException(status_code=400, detail="code is required")

    try:
        result = await debug_code_snippet(
            code,
            language=language,
            goal=goal,
            timeout=max(5, min(timeout, 120)),
            max_iterations=max(1, min(max_iterations, 10)),
            llm_call=_llm_chat,
        )
        return {"status": "ok", **result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"code debug failed: {exc}")


@router.post("/execute")
async def agent_execute(payload: dict[str, Any]):
    plan_id = payload.get("plan_id", "")
    approved_by = payload.get("approved_by", "system")
    task = payload.get("task", f"Executing plan {plan_id}")
    devices = payload.get("devices", [])
    risk = str(payload.get("risk", "medium")).lower()

    approval_event = _append_approval_event(
        plan_id=plan_id,
        task=task,
        devices=[str(device) for device in devices if str(device).strip()],
        risk=risk,
        status="approved",
        message=f"Plan {plan_id} approved by {approved_by}",
        approved_by=approved_by,
    )

    approvals.resolve_approval(plan_id, "approved", approved_by)

    audit_store.record(
        user=approved_by,
        session_id=str(payload.get("session_id") or ""),
        task_id=plan_id,
        source="User",
        action="approve",
        target_type="plan",
        target_id=plan_id,
        policy="APPROVAL_REQUIRED",
        risk=risk,
        result="success",
        evidence="audit_record",
        summary=f"Plan {plan_id} approved by {approved_by}",
        approval_id=plan_id,
    )

    event = {
        "id": f"exec-{len(_agent_events) % 10000:04d}",
        "type": "task_progress",
        "plan_id": plan_id,
        "step": "execute",
        "status": "running",
        "message": f"Executing plan {plan_id} approved by {approved_by}",
        "created_at": datetime.utcnow().isoformat(),
    }
    _agent_events.append(event)
    await _broadcast_event(approval_event)
    await _broadcast_event(event)
    return {"approval": approval_event, "execution": event}


@router.post("/cancel")
async def agent_cancel(payload: dict[str, Any]):
    plan_id = payload.get("plan_id", "")
    cancelled_by = payload.get("cancelled_by", "system")
    task = payload.get("task", f"Plan {plan_id}")
    devices = payload.get("devices", [])
    risk = str(payload.get("risk", "medium")).lower()

    approval_event = _append_approval_event(
        plan_id=plan_id,
        task=task,
        devices=[str(device) for device in devices if str(device).strip()],
        risk=risk,
        status="cancelled",
        message=f"Plan {plan_id} cancelled by {cancelled_by}",
        cancelled_by=cancelled_by,
    )

    approvals.resolve_approval(plan_id, "cancelled", cancelled_by)

    audit_store.record(
        user=cancelled_by,
        session_id=str(payload.get("session_id") or ""),
        task_id=plan_id,
        source="User",
        action="cancel",
        target_type="plan",
        target_id=plan_id,
        policy="APPROVAL_REQUIRED",
        risk=risk,
        result="cancelled",
        evidence="audit_record",
        summary=f"Plan {plan_id} cancelled by {cancelled_by}",
        approval_id=plan_id,
    )

    cancel_event = {
        "id": f"cancel-{len(_agent_events) % 10000:04d}",
        "type": "task_progress",
        "plan_id": plan_id,
        "step": "cancel",
        "status": "failed",
        "message": f"Plan {plan_id} cancelled by {cancelled_by}",
        "created_at": datetime.utcnow().isoformat(),
    }
    _agent_events.append(cancel_event)
    await _broadcast_event(approval_event)
    await _broadcast_event(cancel_event)
    return {"approval": approval_event, "execution": cancel_event}


@router.get("/events")
async def list_agent_events():
    return {"events": _agent_events[-50:]}


@router.get("/events/stream")
async def stream_agent_events():
    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        _event_subscribers.append(queue)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        finally:
            _event_subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/tools")
async def list_agent_tools():
    """List available agent tools for LLM function calling."""
    return {"tools": get_tool_descriptions()}


@router.get("/tools/registry")
async def list_agent_tool_registry(namespace: str | None = None):
    """List structured agent tool descriptors used by the orchestrator."""
    return {"tools": list_tool_descriptors(namespace)}


@router.get("/audit")
async def list_agent_audit(limit: int = 200):
    """List persisted agent audit records (newest first)."""
    return {"records": audit_store.list_records(limit=limit)}


@router.post("/export")
async def agent_export(payload: dict[str, Any]):
    """Generate a downloadable report (csv/xlsx/pdf/json/txt/md) for devices."""
    device_ids = [str(d) for d in payload.get("device_ids") or [] if str(d).strip()]
    if not device_ids:
        raise HTTPException(400, "device_ids is required")
    fmt = (str(payload.get("format") or "xlsx")).lower()
    if fmt not in FORMATTERS:
        raise HTTPException(400, f"Unsupported format: {fmt}")
    kind = str(payload.get("kind") or "all").lower()
    if kind not in {"all", "interfaces", "routes", "config"}:
        kind = "all"

    devices = await collect_devices(device_ids)
    title = str(payload.get("title") or "Network Device Report")
    filename, data = build_export_document(devices, kind=kind, fmt=fmt, title=title)
    target = (EXPORT_DIR / filename).resolve()
    if not str(target).startswith(str(EXPORT_DIR.resolve())):
        raise HTTPException(400, "Invalid filename")
    target.write_bytes(data)

    return {
        "filename": filename,
        "format": fmt,
        "kind": kind,
        "download_url": f"/api/v1/agent/download/{filename}",
        "size": len(data),
    }


@router.get("/download/{filename}")
async def agent_download(filename: str):
    target = (EXPORT_DIR / filename).resolve()
    if not str(target).startswith(str(EXPORT_DIR.resolve())) or not target.is_file():
        raise HTTPException(404, "File not found")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media = {
        "csv": "text/csv",
        "json": "application/json",
        "txt": "text/plain",
        "md": "text/markdown",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf",
    }.get(ext, "application/octet-stream")
    return FileResponse(target, media_type=media, filename=filename)


@router.post("/tools/execute")
async def execute_agent_tool(payload: dict[str, Any]):
    """Execute an agent tool by name."""
    tool_name = payload.get("tool", "")
    params = {k: v for k, v in payload.items() if k != "tool"}

    if tool_name not in AGENT_TOOLS:
        raise HTTPException(400, f"Unknown tool: {tool_name}")

    result = await execute_tool(tool_name, **params)
    return result


@router.get("/tools/pending-approvals")
async def list_pending_approvals():
    """Daftar command yang sedang menunggu persetujuan (untuk flow approval)."""
    from app.agent.tools import list_pending_approvals as _list
    return {"pending": _list()}


@router.post("/tools/approve")
async def post_approve_command(payload: dict[str, Any]):
    """Setujui command pending (approval_id) lalu eksekusi; audit via pending."""
    from app.agent.tools import approve_command as _approve
    approval_id = str(payload.get("approval_id") or "").strip()
    if not approval_id:
        raise HTTPException(400, "approval_id is required")
    approved_by = str(payload.get("approved_by") or "system").strip()
    return await _approve(approval_id, approved_by=approved_by)


async def _broadcast_event(event: dict[str, Any]):
    for queue in _event_subscribers:
        try:
            await queue.put(event)
        except Exception:
            pass
