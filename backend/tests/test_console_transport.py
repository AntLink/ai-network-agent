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
