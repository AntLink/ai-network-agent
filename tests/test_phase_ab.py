"""Unit tests for Phase A+B hardening.

- ConsoleTransport prompt-synced telnet session (mocked socket)
- Bare-ENTER-at-password guard
- CiscoDriver.save_config persistence verification (the '[OK] can lie' fix)
- Flash health detection ('0K CompactFlash' = broken)
- SSHTransport legacy algorithm fallback

Run: python -m pytest tests/test_phase_ab.py -v
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import patch as mock_patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pytest

from app.transports.console import (
    ConsoleAuthError,
    ConsoleTransport,
    PROMPT_RE,
    PASSWORD_TAIL_RE,
)


# ---------------------------------------------------------------------------
# fakes
# ---------------------------------------------------------------------------

class FakeWriter:
    def __init__(self):
        self.sent = b""
        self.closed = False

    def write(self, data: bytes):
        self.sent += data

    def close(self):
        self.closed = True

    async def wait_closed(self):
        return


class FakeReader:
    def __init__(self, chunks):
        self._q = list(chunks)

    async def read(self, n=4096):
        if not self._q:
            await asyncio.sleep(3600)  # block forever -> expect() times out
        return self._q.pop(0)


def make_device():
    return {
        "id": "cisco-iosv-r1",
        "hostname": "R1",
        "management_address": "172.22.45.249",
        "vendor": "cisco",
        "platform": "ios",
        "console_host": "172.22.37.68",
        "console_port": 5006,
    }


IOS_DIALOG = [
    # boot banner + wizard question
    b"\r\nCisco IOS Software, IOSv Version 15.6(2)T\r\n"
    b"Would you like to enter the initial configuration dialog? [yes/no]: ",
    # user EXEC prompt after answering no
    b"\r\nRouter>",
    # enable password challenge
    b"\r\nPassword: ",
    # privileged prompt
    b"\r\nRouter#",
]


@pytest.fixture
def patched_connect(monkeypatch):
    """Replace asyncio.open_connection used inside transports.console."""
    writer = FakeWriter()
    reader = FakeReader(IOS_DIALOG)

    async def fake_open_connection(host, port):
        return reader, writer

    monkeypatch.setattr(
        __import__("app.transports.console", fromlist=["asyncio"]).asyncio,
        "open_connection", fake_open_connection,
    )
    return reader, writer


# ---------------------------------------------------------------------------
# console transport
# ---------------------------------------------------------------------------

def test_console_login_walks_full_dialog(patched_connect):
    reader, writer = patched_connect
    con = ConsoleTransport("1.2.3.4", 5006, password="Admin123!",
                           enable_password="Admin123!", char_delay=0)

    asyncio.run(con.open())

    sent = writer.sent.decode(errors="replace")
    assert "no\r" in sent, "must answer wizard with 'no'"
    assert "enable\r" in sent, "must escalate to privileged mode"
    assert sent.count("Admin123!\r") >= 1, "password must be submitted"


def test_console_run_returns_cleaned_output(patched_connect):
    reader, writer = patched_connect
    # append command echo + body + prompt for the exec phase
    reader._q.extend([
        b"show version\r\nCisco IOS Software, IOSv Version 15.6(2)T\r\nRouter#",
    ])
    con = ConsoleTransport("1.2.3.4", 5006, password="pw", char_delay=0)

    out = asyncio.run(con.run("show version"))
    assert "Cisco IOS Software" in out
    assert not out.strip().endswith("Router#"), "prompt must be stripped"


def test_console_refuses_bare_enter_at_password(patched_connect):
    reader, writer = patched_connect
    con = ConsoleTransport("1.2.3.4", 5006, password="pw", char_delay=0)
    con.reader, con.writer = reader, writer
    con.buf = "...some output...\r\nPassword: "
    with pytest.raises(ConsoleAuthError):
        asyncio.run(con.send_line(""))


def test_password_regex_matches_lab_prompts():
    assert PASSWORD_TAIL_RE.search("Password: ")
    assert PASSWORD_TAIL_RE.search("Username: ")
    assert PROMPT_RE.search("Router(config-if)#")


# ---------------------------------------------------------------------------
# save_config verification + flash health
# ---------------------------------------------------------------------------

def _driver_with_exec(monkeypatch, outputs_by_marker):
    from app.drivers.cisco.driver import CiscoDriver
    drv = CiscoDriver(make_device())

    async def fake_exec(cmd):
        for marker, out in outputs_by_marker.items():
            if marker in cmd:
                return out
        return ""

    monkeypatch.setattr(drv, "_exec", fake_exec)
    return drv


def test_save_config_verified_when_startup_matches(monkeypatch):
    drv = _driver_with_exec(monkeypatch, {
        "write memory": "Building configuration...[OK]",
        "running-config | include ^hostname": "hostname R1",
        "startup-config | include ^hostname": "hostname R1",
    })
    res = asyncio.run(drv.save_config())
    assert res["saved"] is True and res["verified"] is True


def test_save_config_detects_lying_ok(monkeypatch):
    """Broken-flash lab scenario: [OK] printed but nothing persisted."""
    drv = _driver_with_exec(monkeypatch, {
        "write memory": "Building configuration...[OK]",
        "running-config | include ^hostname": "hostname R1",
        "startup-config | include ^hostname": "%Error opening flash0:/",
    })
    res = asyncio.run(drv.save_config())
    assert res["saved"] is False and res["verified"] is False
    assert "false" in res["reason"].lower()


def test_health_detects_broken_flash(monkeypatch):
    drv = _driver_with_exec(monkeypatch, {
        "show version": (
            "262144K bytes of flash ... \n"
            "0K bytes of ATA System CompactFlash 0\n"
        ),
    })

    async def fake_tcp(host, port):
        class W:
            def close(self): pass
        class R:
            async def readline(self): return b"SSH-2.0-Cisco\n"
        return R(), W()

    with mock_patch("asyncio.open_connection", fake_tcp):
        res = asyncio.run(drv.health())
    assert res["reachable"] is True
    assert res["flash_ok"] is False, "0K compactflash must be flagged broken"


def test_health_ok_flash(monkeypatch):
    drv = _driver_with_exec(monkeypatch, {
        "show version": "262144K bytes of ATA System CompactFlash 0\n",
    })

    async def fake_tcp(host, port):
        class W:
            def close(self): pass
        class R:
            async def readline(self): return b"SSH-2.0-Cisco\n"
        return R(), W()

    with mock_patch("asyncio.open_connection", fake_tcp):
        res = asyncio.run(drv.health())
    assert res["flash_ok"] is True


# ---------------------------------------------------------------------------
# ssh legacy fallback
# ---------------------------------------------------------------------------

def test_ssh_fallback_merges_legacy_algorithms(monkeypatch):
    import app.transports.ssh as tssh

    calls = []

    class FakeConn:
        def __enter__(self): return self
        def __exit__(self, *a): return False

    async def fake_connect(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("Key exchange failed: no matching kex")
        return FakeConn()

    monkeypatch.setattr(tssh.asyncssh, "connect", fake_connect)

    t = tssh.SSHTransport(
        "10.0.0.9", "admin", "pw",
        connect_options={"kex_algs": ["curve25519-sha256"]},
    )
    conn = asyncio.run(t._connect_resilient())

    assert isinstance(conn, FakeConn)
    assert len(calls) == 2, "exactly one legacy retry expected"
    retry_kex = calls[1]["kex_algs"]
    assert "curve25519-sha256" in retry_kex, "caller options preserved"
    assert "diffie-hellman-group14-sha1" in retry_kex, "legacy appended"


def test_ssh_fallback_disabled(monkeypatch):
    import app.transports.ssh as tssh

    async def fake_connect(**kwargs):
        raise RuntimeError("Key exchange failed")

    monkeypatch.setattr(tssh.asyncssh, "connect", fake_connect)

    t = tssh.SSHTransport("10.0.0.9", "admin", "pw", legacy_fallback=False)
    with pytest.raises(RuntimeError):
        asyncio.run(t._connect_resilient())


# ---------------------------------------------------------------------------
# inventory wiring
# ---------------------------------------------------------------------------

def test_inventory_has_console_fields():
    import json
    inv = json.loads(
        (Path(__file__).resolve().parents[1] / "inventory" / "devices.json").read_text()
    )
    by_id = {d["id"]: d for d in inv["devices"]}
    for dev_id, port in [
        ("cisco-iosv-r1", 5006),
        ("cisco-iosv-r2", 5008),
        ("cisco-iosvl2-sw1", 5002),
        ("cisco-iosvl2-sw2", 5004),
    ]:
        d = by_id[dev_id]
        assert d.get("console_host") == "172.22.46.196"
        assert d.get("console_port") == port
