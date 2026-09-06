import asyncio

from app.transports.console import ConsoleTransport


class DummyWriter:
    def __init__(self):
        self.writes = []

    def write(self, data: bytes):
        self.writes.append(data)

    async def drain(self):
        return None


def test_strip_telnet_removes_iac_negotiation_bytes():
    raw = b"\xff\xfb\x01MikroTik Login:\xff\xfb\x03"

    assert ConsoleTransport._strip_telnet(raw) == b"MikroTik Login:"


def test_clean_removes_routeros_private_ansi_sequences():
    raw = "\x1bc\x1b[?7lMikroTik Login:"

    assert ConsoleTransport.clean(raw) == "MikroTik Login:"


def test_expect_detects_alpine_shell_prompt():
    async def run():
        transport = ConsoleTransport("127.0.0.1", 5000)
        transport.buf = "localhost:~#"
        assert await transport.expect(timeout=0.1) == "prompt"

    asyncio.run(run())


def test_clean_command_output_removes_alpine_shell_prompt():
    raw = "localhost:~# echo READY\nREADY\nlocalhost:~#"
    assert ConsoleTransport.clean_command_output(raw, "echo READY") == "READY"


def test_telnet_negotiation_does_not_reply_to_duplicate_options():
    transport = ConsoleTransport("127.0.0.1", 5000)
    writer = DummyWriter()
    transport.writer = writer

    transport._negotiate_telnet(b"\xff\xfb\x01\xff\xfb\x03\xff\xfb\x00\xff\xfd\x00")
    transport._negotiate_telnet(b"\xff\xfb\x03")

    assert writer.writes == [
        b"\xff\xfd\x01",
        b"\xff\xfd\x03",
        b"\xff\xfd\x00",
        b"\xff\xfb\x00",
    ]


def test_bootstrap_password_falls_back_when_same_as_old():
    transport = ConsoleTransport(
        "127.0.0.1",
        5000,
        bootstrap_password="admin",
    )

    transport.buf = "new password> "
    assert transport._next_bootstrap_password() == "admin"
    transport.buf = "T\nr\ny\n \na\ng\na\ni\nn\n, error: New password is the same as old one\nnew password> "
    assert transport._next_bootstrap_password() == "admin123"
    transport.buf = "r\ne\np\ne\na\nt\n \nn\ne\nw\n \np\na\ns\ns\nw\no\nr\nd\n>\n "
    assert transport._next_bootstrap_password() == "admin123"


def test_expect_detects_routeros_new_password_prompt_with_split_letters():
    async def run():
        transport = ConsoleTransport("127.0.0.1", 5000)
        transport.buf = "n\ne\nw\n \np\na\ns\ns\nw\no\nr\nd\n>\n "
        assert await transport.expect(timeout=0.1) == "newpass"

    asyncio.run(run())


def test_clean_command_output_removes_stale_routeros_prompts_and_duplicate_echo():
    raw = """[admin@MikroTik] >                                                             [admin@MikroTik] > [admin@MikroTik] >
[admin@MikroTik] > /interface print detail[admin@MikroTik] > /interface print detail
Flags: D - DYNAMIC; X - DISABLED; I - INACTIVE, R - RUNNING; S - SLAVE;
 0   R   name="ether1" default-name="ether1" type="ether" mtu=1500
         actual-mtu=1500 vrf=main mac-address=0C:1E:F6:E4:00:00
-- [Q quit|D dump|down]
[admin@MikroTik] >
"""

    out = ConsoleTransport.clean_command_output(raw, "/interface print detail")

    assert out.startswith("Flags: D - DYNAMIC")
    assert 'name="ether1"' in out
    assert "[admin@MikroTik]" not in out
    assert "/interface print detail" not in out
    assert "Q quit" not in out


def test_expect_detects_routeros_dump_pager_as_more():
    async def run():
        transport = ConsoleTransport("127.0.0.1", 5000)
        transport.buf = 'name="ether7" type="ether"\n-- [Q quit|D dump|down]'
        assert await transport.expect(timeout=0.1) == "more"

    asyncio.run(run())


def test_command_without_paging_is_added_only_for_routeros_print():
    assert (
        ConsoleTransport.command_without_paging("/interface print detail")
        == "/interface print detail without-paging"
    )
    assert (
        ConsoleTransport.command_without_paging("/interface print detail without-paging")
        == "/interface print detail without-paging"
    )
    assert ConsoleTransport.command_without_paging("show ip interface brief") == "show ip interface brief"


def test_clean_command_output_preserves_cisco_style_output():
    raw = """Router#show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     10.0.0.1        YES manual up                    up
Router#
"""

    out = ConsoleTransport.clean_command_output(raw, "show ip interface brief")

    assert out.startswith("Interface")
    assert "GigabitEthernet0/0" in out
    assert "Router#" not in out
    assert "show ip interface brief" not in out
