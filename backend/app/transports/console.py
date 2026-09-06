"""Telnet console transport (GNS3/aux/out-of-band consoles).

Fallback path when device SSH is broken or unavailable. Learned from the
2026-08-23 GNS3 recovery session:

- Send commands only AFTER the prompt is ready; wait for it again before
  the next command (prompt-synced, never fixed sleeps).
- NEVER send a bare ENTER while the last line ends with ':' - at a
  'Password:' prompt that submits an empty password and fails auth.
- Virtual consoles swallow keystrokes while boot output streams; slow
  char-by-char sending with tiny delays is the reliable approach.
- Initial config wizard must be answered with 'no' before configuring.
"""
import asyncio
import re
import time
from contextlib import asynccontextmanager

from app.core.audit import log_event
from app.drivers.cisco.cli import clean_cli_output

# IOS-style exec/config prompt: hostname(config-if)# etc.
# Robustness: '-' in the name char class must be escaped (>>> '-'), otherwise
# it is read as the range char of an empty/`>-` class; and FortiOS-style
# prompts carry a SPACE before the marker ("FortiFirewall-VM64-KVM # "), so an
# optional whitespace run is allowed before the closing [#>].
PROMPT_RE = re.compile(r"[A-Za-z0-9().$\-#]+(?:\s+)?[#>]\s*$")
# BusyBox/Alpine shell prompt, e.g. `localhost:~#` or `root@alpine:~#`.
SHELL_PROMPT_RE = re.compile(r"(?:[A-Za-z0-9._-]+@)?[A-Za-z0-9._-]+:[^\r\n#>]*[#>]\s*$")
# RouterOS prompt: [admin@MikroTik] >  (atau dengan menu, mis. [admin@MikroTik] /ip >)
ROUTEROS_PROMPT_RE = re.compile(r"\]\s*>\s*$")
# Tail-anchored variants (match only at END of received stream):
PASSWORD_TAIL_RE = re.compile(r"(?:Password|password|Username|username|login)\s*:\s*$")
# Position-free variants for dialog scanning:
LOGIN_ANYWHERE_RE = re.compile(r"(?:[Ll]ogin|[Uu]sername)\s*:")
PASSWORD_ANYWHERE_RE = re.compile(r"(?:Password|password)\s*:")
YESNO_ANYWHERE_RE = re.compile(r"\[yes/no\]")
# AOS-CX style confirmation: "Do you want to continue (y/n)?" etc.
# Answered with 'n' (decline) so we never commit destructive actions silently.
YN_ANYWHERE_RE = re.compile(r"[\(\[]\s*[yYnN]\s*/\s*[yYnN]\s*[\)\]]")
# Generic confirmation prompts: "Destination filename [x]? ", "[confirm] ", etc.
CONFIRM_ANYWHERE_RE = re.compile(r"(\[confirm\]|[\[\(][^\]\)]*[\]\)]\s*\?)\s*$")
MORE_RE = re.compile(r"(?:--\s?More\s?--|--\s*\[Q quit\|D dump\|down\])\s*$")
RETURN_RE = re.compile(r"Press RETURN to get started")
# RouterOS CHR first-boot, antes:
#   "Do you want to see the software license? [y/n]:"  -> jawab n (skip)
#   "Do you accept the license agreement? [y/n]:"      -> jawab y (terima)
# Tail-anchored agar tidak memicu di teks isi EULA.
LICENSE_SEE_RE = re.compile(
    r"want to see\b.*\blicense[^\n]*\??\s*\[?[yYnN]\s*/\s*[yYnN]\]?\s*:\s*$", re.I)
LICENSE_ACCEPT_RE = re.compile(
    r"accept\b.*\blicense[^\n]*\??\s*\[?[yYnN]\s*/\s*[yYnN]\]?\s*:\s*$", re.I)
# RouterOS CHR 7.x first-boot menu justru: "License [Y/n]:" -> jawab n
LICENSE_YN_RE = re.compile(r"\blicense\b[^\n]*\[[yYnN]\s*/\s*[yYnN]\]\s*[:>]\s*$", re.I)
# RouterOS first-boot: wizard set password admin
#   "New password:"  -> kirim bootstrap password
#   "Confirm new password:" -> kirim ulang bootstrap password
NEWPASSWORD_RE = re.compile(
    r"(?:new password|repeat new password|confirm(?: new)? password)[^\n]{0,16}$", re.I)


_CONSOLE_LOCKS: dict[tuple[int, str, int], asyncio.Lock] = {}


def _console_lock(host: str, port: int) -> asyncio.Lock:
    """Serialize console sessions per (host, port) inside one event loop.

    A telnet console is a single-writer resource: two concurrent sessions
    interleave their keystrokes on the same port, mangling commands and
    leaving the device stuck mid-dialog (seen live: ASAv/switch corrupted).
    """
    key = (id(asyncio.get_running_loop()), host, port)
    lock = _CONSOLE_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _CONSOLE_LOCKS[key] = lock
    return lock


class ConsoleTransportError(Exception):
    pass


class ConsoleTimeoutError(ConsoleTransportError):
    pass


class ConsoleAuthError(ConsoleTransportError):
    pass


class _StdinWriter:
    """Mimics asyncssh stdin: accepts str, encodes internally."""

    def __init__(self, transport: "ConsoleTransport"):
        self._t = transport

    def write(self, data: str):
        self._t._raw_send(data)

    async def drain(self):
        await asyncio.sleep(0)


class _StdoutReader:
    """Mimics asyncssh stdout.read(n) -> str."""

    def __init__(self, transport: "ConsoleTransport"):
        self._t = transport

    async def read(self, n: int = 4096) -> str:
        return await self._t._recv_chunk(timeout=0.5)


class _ProcAdapter:
    """Duck-typed replacement for an asyncssh process object so the
    existing cli.py helpers (drain_prompt, run_batch, ...) work unchanged."""

    def __init__(self, transport: "ConsoleTransport"):
        self.stdin = _StdinWriter(transport)
        self.stdout = _StdoutReader(transport)

    async def wait(self):
        return 0


class ConsoleTransport:
    """Prompt-synced telnet console session.

    One connection per operation (open -> login dialog -> run -> close),
    mirroring how SSHTransport.run opens a fresh connection each time.
    """

    ANSI_RE = re.compile(r"(?:\x1b|\x9b)(?:\[[0-9;?]*[ -/]*[@-~]|[@-~])")
    CTRL_RE = re.compile(r"[\x00-\x08\x0b-\x1f]")

    def __init__(
        self,
        host: str,
        port: int,
        password: str | None = None,
        enable_password: str | None = None,
        username: str | None = None,
        enable: bool = False,
        allow_empty_password: bool = False,
        bootstrap_password: str | None = None,
        login_timeout: float = 30.0,
        char_delay: float = 0.04,
        device_id: str = "",
        pager_off_command: str | None = None,
    ):
        self.host = host
        self.port = port
        self.password = password
        self.enable_password = enable_password if enable_password is not None else password
        self.username = username
        self.enable = enable
        self.allow_empty_password = allow_empty_password
        self.bootstrap_password = bootstrap_password
        self.login_timeout = login_timeout
        self.char_delay = char_delay
        self.device_id = device_id
        self.pager_off_command = pager_off_command
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.buf = ""
        # scan cursor: patterns are searched only in buf[_pos:], so handled
        # dialog text cannot re-trigger (stale wizard questions/prompts)
        self._pos = 0
        self._session_start = 0
        self._cred_stage = 0
        self._user_sent = False
        self._telnet_replies_sent: set[tuple[int, int]] = set()
        self._bootstrap_index = 0
        self._pending_bootstrap_password: str | None = None
        self._enable_attempted = False
        self._auth_attempts = 0
        self._password_sent = False
        self._lock: asyncio.Lock | None = None

    # ------------------------------------------------------------------
    # low-level I/O
    # ------------------------------------------------------------------

    @staticmethod
    def clean(raw: str) -> str:
        raw = ConsoleTransport.ANSI_RE.sub("", raw)
        return ConsoleTransport.CTRL_RE.sub("", raw)

    @staticmethod
    def clean_command_output(raw: str, command: str | None = None) -> str:
        """Return only command body, without stale prompts or command echoes."""
        text = clean_cli_output(raw, command)
        if command:
            idx = text.rfind(command.strip())
            if idx >= 0:
                text = text[idx + len(command.strip()):]
        text = text.replace("\r", "")
        text = re.sub(r"(?m)^\s*\[[^\]\r\n]+]\s*>\s*", "", text)
        text = re.sub(r"(?m)^\s*[A-Za-z0-9().-]+[#>]\s*", "", text)
        # remove leftover pager markers that answering --More-- leaves behind.
        # IOSv: "<--- More --->", MikroTik: "-- More --", ASA: "---- More ----".
        text = re.sub(r"(?i)(?:<---\s*More\s*--->|----\s*More\s*----|--\s*More\s*-+)", "", text)
        text = re.sub(r"(?im)^\s*(--\s?More\s?--|----\sMore\s----|\s*--\s*$)", "", text)
        # IOSv console pager redraw leaves an 8-9 space column indent on the
        # line that was under the "<--- More --->" prompt when we sent space.
        text = re.sub(r"(?m)^ {8,}", "", text)
        lines = text.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and (
            not lines[-1].strip()
            or ROUTEROS_PROMPT_RE.search(lines[-1].strip())
            or SHELL_PROMPT_RE.search(lines[-1].strip())
            or PROMPT_RE.search(lines[-1].strip())
            or MORE_RE.search(lines[-1].strip())
        ):
            lines.pop()
        return "\n".join(lines).strip()

    @staticmethod
    def command_without_paging(command: str) -> str:
        """Disable RouterOS pager for print commands while keeping other CLIs unchanged.

        RouterOS 7.x quirk: on filtered prints (`/file print where ...`) the
        appended `without-paging` makes the output come back EMPTY, so commands
        that already carry a `where` clause are left untouched.
        """
        stripped = command.strip()
        if (
            stripped.startswith("/")
            and re.search(r"(^|\s)print(\s|$)", stripped)
            and not re.search(r"(^|\s)without-paging(\s|$)", stripped)
            and not re.search(r"\bwhere\b", stripped)
        ):
            return f"{stripped} without-paging"
        return command

    async def _type_slow(self, text: str, delay: float = 0.06, newline: bytes = b"\r"):
        """Ketik pelan per-karakter + Enter.

        CHR/GNS3 sering menelan input cepat saat banner masih render;
        ketik pelan (seperti manusia) jauh lebih andal untuk login/wizard.
        """
        for ch in text:
            self.writer.write(ch.encode())
            try:
                await asyncio.wait_for(self.writer.drain(), timeout=2.0)
            except Exception:
                pass
            await asyncio.sleep(delay)
        self.writer.write(newline)
        try:
            await asyncio.wait_for(self.writer.drain(), timeout=2.0)
        except Exception:
            pass

    async def _settle(self, seconds: float = 0.5):
        await self._recv_chunk(timeout=1.0)
        await asyncio.sleep(seconds)

    def _raw_send(self, text: str):
        if not self.writer:
            raise ConsoleTransportError("console not connected")
        self.writer.write(text.encode("utf-8"))

    async def _recv_chunk(self, timeout: float = 0.5) -> str:
        try:
            piece = await asyncio.wait_for(self.reader.read(4096), timeout=timeout)
        except (asyncio.TimeoutError, AttributeError):
            return ""
        if not piece:
            return ""
        self._negotiate_telnet(piece)
        self._answer_terminal_queries(piece)
        chunk = self.clean(self._strip_telnet(piece).decode("utf-8", errors="replace"))
        self.buf += chunk
        return chunk

    @staticmethod
    def _strip_telnet(raw: bytes) -> bytes:
        """Remove telnet IAC control sequences before text prompt parsing."""
        out = bytearray()
        i = 0
        n = len(raw)
        while i < n:
            if raw[i] != 0xFF:
                out.append(raw[i])
                i += 1
                continue
            if i + 1 >= n:
                break
            cmd = raw[i + 1]
            if cmd == 0xFF:
                out.append(0xFF)
                i += 2
            elif cmd in (0xFB, 0xFC, 0xFD, 0xFE):
                i += 3
            elif cmd == 0xFA:
                end = raw.find(b"\xff\xf0", i + 2)
                i = n if end == -1 else end + 2
            else:
                i += 2
        return bytes(out)

    def _answer_terminal_queries(self, raw: bytes):
        """Jawab query terminal yang dikirim device (mis. RouterOS saat login).

        ESC[6n / ESC[?6n = DSR (cursor position request); tanpa jawaban
        ESC[row;colR, login RouterOS menggantung. Balas; ANSI ini tidak masuk
        buf (di-clean).
        """
        if not self.writer or b"\x1b" not in raw:
            return
        if b"\x1b[6n" in raw or b"\x1b[?6n" in raw:
            self.writer.write(b"\x1b[1;1R")
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.writer.drain())
            except Exception:
                pass

    def _negotiate_telnet(self, raw: bytes):
        """Balas negosiasi telnet IAC (kunci biar RouterOS bersedia terima input).

        Server telnet mengirim IAC WILL/DONT/DO/DONT <option> saat connect.
        Klien asli (PuTTY) membalas; tanpa balasan, beberapa server (mis.
        RouterOS CHR) berperilaku seolah input tidak diproses. Kami membalas:
        - WILL opt  -> DO opt   (terima)
        - WONT opt  -> DONT opt
        - DO opt    -> WILL opt
        - DONT opt  -> WONT opt
        """
        if not self.writer or b"\xff" not in raw:
            return
        i = 0
        n = len(raw)
        sent = False
        while i + 2 < n:
            if raw[i] == 0xFF and raw[i + 1] in (0xFB, 0xFC, 0xFD, 0xFE):
                cmd, opt = raw[i + 1], raw[i + 2]
                if cmd == 0xFB:      # WILL
                    reply = b"\xff\xfd" + bytes([opt])
                elif cmd == 0xFC:    # WONT
                    reply = b"\xff\xfe" + bytes([opt])
                elif cmd == 0xFD:    # DO
                    reply = b"\xff\xfb" + bytes([opt])
                else:                # DONT
                    reply = b"\xff\xfc" + bytes([opt])
                key = (cmd, opt)
                if key not in self._telnet_replies_sent:
                    self._telnet_replies_sent.add(key)
                    self.writer.write(reply)
                    sent = True
                i += 3
                continue
            i += 1
        if sent:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.writer.drain())
            except Exception:
                pass

    async def send_line(self, text: str):
        """Send a line slowly, char by char, then CR.

        Guard rail from the lab: a bare ENTER ('\r') sent while output ends
        with ':' becomes an empty password submission - refuse it.
        """
        if text == "" and PASSWORD_TAIL_RE.search(self.buf[-120:]):
            raise ConsoleAuthError(
                "refusing bare ENTER at a credential prompt "
                "(would submit empty password)"
            )
        for ch in text:
            self._raw_send(ch)
            await asyncio.sleep(self.char_delay)
        self._raw_send("\r")
        await asyncio.sleep(self.char_delay * 4)

    async def _send_password(self, password: str):
        """Type a password slowly with pauses, so console chars don't collide.

        Lab lesson: typing a password too fast at the prompt causes the console
        to merge/tangle characters with the echo. Pause before typing, between
        characters, and before hitting Enter.
        """
        await self._settle(0.4)
        for ch in password:
            self._raw_send(ch)
            try:
                await self.writer.drain()
            except Exception:
                pass
            await asyncio.sleep(0.1)
        await self._settle(0.3)
        self._raw_send("\r")
        try:
            await self.writer.drain()
        except Exception:
            pass
        await self._settle(0.4)

    # ------------------------------------------------------------------
    # dialog engine
    # ------------------------------------------------------------------

    async def expect(self, timeout: float) -> str:
        """Read until a recognizable state appears.

        Priority matters (lab lesson): boot output can contain STALE text -
        e.g. a previous session's prompt echoed above an unanswered wizard
        question. Credential/yes-no/--More-- states are therefore detected
        BEFORE trusting a prompt match.
        """
        deadline = time.perf_counter() + timeout
        local = ""
        patterns = (
            ("newpass", NEWPASSWORD_RE),
            ("login", LOGIN_ANYWHERE_RE),
            ("password", PASSWORD_ANYWHERE_RE),
            ("license_yn", LICENSE_YN_RE),
            ("license_accept", LICENSE_ACCEPT_RE),
            ("license_see", LICENSE_SEE_RE),
            ("yesno", YN_ANYWHERE_RE),
            ("yesno", YESNO_ANYWHERE_RE),
            ("confirm", CONFIRM_ANYWHERE_RE),
            ("more", MORE_RE),
            ("prompt", ROUTEROS_PROMPT_RE),
            ("prompt", SHELL_PROMPT_RE),
            ("prompt", PROMPT_RE),
        )
        while time.perf_counter() < deadline:
            window = self.buf[self._pos:]
            # RouterOS can render a prompt one character per line. Compact
            # detection must run before generic prompt matching, otherwise
            # the trailing `>` is mistaken for an ordinary prompt.
            compact = re.sub(r"[\s\x00-\x1f\ufffd]+", "", window).lower()
            if (
                "newpassword:" in compact
                or "newpassword>" in compact
                or "repeatnewpassword:" in compact
                or "repeatnewpassword>" in compact
                or "confirmnewpassword:" in compact
                or "confirmnewpassword>" in compact
            ):
                self._pos = len(self.buf)
                return "newpass"
            for name, rx in patterns:
                m = rx.search(window)
                if m:
                    self._pos += m.end()
                    return name
            chunk = await self._recv_chunk(timeout=0.4)
            local += chunk
        raise ConsoleTimeoutError(f"no expected pattern within {timeout}s; tail={local[-200:]!r}")

    async def open(self):
        if self.writer:
            return
        lock = _console_lock(self.host, self.port)
        try:
            await asyncio.wait_for(lock.acquire(), timeout=self.login_timeout)
        except asyncio.TimeoutError:
            raise ConsoleTimeoutError(
                f"console {self.host}:{self.port} busy (another console session active)"
            )
        self._lock = lock
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.login_timeout,
            )
        except Exception as e:
            self._release_console_lock()
            raise ConsoleTransportError(
                f"cannot connect to console {self.host}:{self.port}: {e}"
            ) from e
        self.buf = ""
        self._pos = 0
        try:
            await self._provoked_login()
        except Exception:
            await self.close()
            raise

    async def _has_known_state(self) -> bool:
        window = self.buf[self._pos:]
        return bool(
            LOGIN_ANYWHERE_RE.search(window)
            or PASSWORD_ANYWHERE_RE.search(window)
            or YESNO_ANYWHERE_RE.search(window)
            or MORE_RE.search(window)
            or PROMPT_RE.search(window)
        )

    async def _provoked_login(self):
        """Wake up a silent console first, then run the dialog.

        Idle telnet consoles print nothing until a key arrives (the prompt
        is already sitting there unrendered). A provoking ENTER solves it -
        but never when the screen already sits at a credential prompt. Retry
        a few times because the first connection to a sleeping GNS3 node can
        be slow to render output.
        """
        await self._recv_chunk(timeout=5.0)
        if RETURN_RE.search(self.buf):
            self._raw_send("\r")          # 'Press RETURN to get started'
            await self._recv_chunk(timeout=2.0)
        attempts = 0
        while not await self._has_known_state() and attempts < 4:
            attempts += 1
            self._raw_send("\r")          # provoke hidden prompt
            await self._recv_chunk(timeout=2.5)
        await self._login()
        # everything before this point is login noise, not command output
        self._session_start = self._pos

    async def _send_username(self):
        await self._type_slow(self.username or "", newline=b"\r")
        self._user_sent = True

    def _bootstrap_candidates(self) -> list[str]:
        candidates: list[str] = []
        for value in (self.bootstrap_password, "admin123"):
            if value and value not in candidates:
                candidates.append(value)
        return candidates

    def _next_bootstrap_password(self) -> str:
        tail = self.buf[-240:].lower()
        compact_tail = re.sub(r"[\s\x00-\x1f\ufffd]+", "", tail)
        candidates = self._bootstrap_candidates()
        if not candidates:
            raise ConsoleAuthError("new-password prompt but no bootstrap_password configured")
        if "sameasold" in compact_tail or "tryagain" in compact_tail:
            self._bootstrap_index = min(self._bootstrap_index + 1, len(candidates) - 1)
            self._pending_bootstrap_password = None
        if "repeatnewpassword" in compact_tail or "confirmnewpassword" in compact_tail:
            return self._pending_bootstrap_password or candidates[self._bootstrap_index]
        password = candidates[self._bootstrap_index]
        self._pending_bootstrap_password = password
        return password

    async def close(self):
        try:
            if self.writer:
                self.writer.close()
                try:
                    await self.writer.wait_closed()
                except Exception:
                    pass
        finally:
            self.writer = None
            self.reader = None
            self._release_console_lock()

    def _release_console_lock(self):
        lock, self._lock = self._lock, None
        if lock is not None and lock.locked():
            try:
                lock.release()
            except RuntimeError:
                pass

    async def _login(self):
        """Walk the boot/login dialog until we own an exec prompt.

        Handles: 'Press RETURN', initial wizard '[yes/no]', username/password
        prompts, and privilege escalation via 'enable'.
        Initial recv/provocation already done by _provoked_login().
        """
        deadline = time.perf_counter() + self.login_timeout
        self._auth_attempts = 0
        while time.perf_counter() < deadline:
            try:
                event = await self.expect(timeout=5.0)
            except ConsoleTimeoutError:
                # masih booting/streaming (mis. Cisco/ASA): lanjut baca
                continue

            if event == "prompt":
                tail = self.buf[self._pos - 40:].replace("\r", "")
                if "config" in tail and ")" in tail:
                    # console baru yang mewarisi layar tertinggal di config-mode:
                    # keluar dulu ke EXEC (Ctrl-Z aman di kedua mode).
                    self._raw_send("\x1a")
                    try:
                        await self.writer.drain()
                    except Exception:
                        pass
                    self._pos = len(self.buf)
                    continue
                if (
                    tail.rstrip().endswith(">")
                    and self.enable
                    and not self._enable_attempted
                    and (self.enable_password or self.allow_empty_password)
                ):
                    # sekali saja: bila enable ditolak (Bad passwords) loop harus
                    # berhenti dan kembali ke user mode, bukan mengulang terus.
                    self._enable_attempted = True
                    await self._enter_enable()
                    continue
                log_event(self.device_id or "-", "CONSOLE-LOGIN", "OK", status="OK")
                return
            if event == "newpass":
                # wizard set password baru (RouterOS first-boot)
                await self._settle()
                await self._type_slow(self._next_bootstrap_password())
                continue
            if event == "login":
                await self._settle()
                if self._user_sent and not self._password_sent:
                    # RouterOS merender ulang "MikroTik Login:" saat kita
                    # membalas query telnet/DSR; ini bukan dialog baru.
                    # Jangan kirim ulang username hingga password dikirim.
                    continue
                # login diminta ulang setelah kredensial salah => percobaan baru
                self._auth_attempts += 1
                if self._auth_attempts > 3:
                    raise ConsoleAuthError(
                        "authentication failed (check username/password)"
                    )
                if not self.username:
                    raise ConsoleAuthError("login prompt but no username configured")
                self._user_sent = True
                self._password_sent = False
                await self._send_username()
                continue
            if event == "password":
                await self._settle()
                cred = self._next_login_password()
                if cred is None:
                    raise ConsoleAuthError("password prompt but no password configured")
                if cred == "":
                    self.writer.write(b"\r")  # password kosong (admin CHR)
                    try:
                        await self.writer.drain()
                    except Exception:
                        pass
                else:
                    await self._send_password(cred)
                self._password_sent = True
                continue
            if event == "license_yn":
                await self._settle()
                await self._type_slow("n")  # CHR: "License [Y/n]" -> n (skip)
                continue
            if event == "license_accept":
                await self._settle()
                await self._type_slow("y")  # terima lisensi
                continue
            if event == "license_see":
                await self._settle()
                await self._type_slow("n")  # skip menampilkan EULA
                continue
            if event == "yesno":
                await self.send_line("no")  # never enter setup wizard
                continue
            if event == "confirm":
                self._raw_send("\r")  # accept default (press Enter)
                continue
            if event == "more":
                tail = self.buf[self._pos - 80:self._pos].lower()
                self._raw_send("D" if "q quit" in tail and "d dump" in tail else " ")
                try:
                    await self.writer.drain()
                except Exception:
                    pass
                continue

        raise ConsoleTimeoutError("login dialog did not reach a CLI prompt")

    def _next_login_password(self) -> str | None:
        """Candidate password order for a (re)login dialog.

        Order: configured password -> bootstrap password -> Enter (empty,
        per ASA first-login: no password yet) -> admin123 (MikroTik default).
        Returns None when all candidates are exhausted (caller raises a clean
        auth error instead of looping forever).
        """
        candidates: list[str] = []
        pw = self.password or ""
        if pw:
            candidates.append(pw)
        if self.bootstrap_password and self.bootstrap_password not in candidates:
            candidates.append(self.bootstrap_password)
        if self.allow_empty_password:
            candidates.append("")
        if "admin123" not in candidates:
            candidates.append("admin123")
        # _auth_attempts sudah +1 saat prompt "login" muncul, jadi prompt
        # password pertama pakai idx 0.
        idx = max(0, self._auth_attempts - 1)
        if idx >= len(candidates):
            return None
        return candidates[idx]

    def _next_credential(self, stage: str) -> str | None:
        """Answer order: username/password prompts then enable secret.
        Empty credentials are never returned (empty password trap)."""
        if stage == "enable":
            cred = self.enable_password or ""
            self._cred_stage += 1
            return cred or None
        if stage == "user" and self.username and not self._user_sent:
            # RouterOS/others: 'MikroTik Login:' asks the USERNAME first.
            self._user_sent = True
            return self.username
        cred = self.password or ""
        self._cred_stage += 1
        return cred or None

    async def _enter_enable(self):
        self._raw_send("enable\r")
        await self._recv_chunk(timeout=1.0)
        event = await self.expect(timeout=8.0)
        if event == "password":
            if self.enable_password:
                await self._send_password(self.enable_password)
            elif self.allow_empty_password:
                self.writer.write(b"\r")  # secret kosong (mis. ASAv lab)
                try:
                    await self.writer.drain()
                except Exception:
                    pass
            else:
                raise ConsoleAuthError("enable asks password but none configured")
        elif event != "prompt":
            raise ConsoleAuthError("enable flow stuck")

    # ------------------------------------------------------------------
    # public API (mirrors SSHTransport surface used by cli.py/driver.py)
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def interactive(self, term_size=None):
        await self.open()
        proc = _ProcAdapter(self)
        try:
            yield proc
        finally:
            await self.close()

    async def run(self, command: str) -> str:
        """Run one EXEC command on a fresh console session. Cleaned output."""
        t0 = time.perf_counter()
        try:
            await self.open()
            # biarkan console tenang sebelum kirim perintah (anti hilang-karakter)
            await self._recv_chunk(timeout=1.0)
            await asyncio.sleep(0.2)
            # matikan pager dulu (IOS: terminal length 0, ASA: terminal pager 0)
            # supaya output panjang tidak memicu --More-- / "<--- More --->".
            if self.pager_off_command:
                await self.send_line(self.pager_off_command)
                await self._drain_to_prompt(deadline=time.perf_counter() + 20.0)
                await asyncio.sleep(0.1)
            send_command = self.command_without_paging(command)
            await self.send_line(send_command)
            await self._drain_to_prompt(deadline=time.perf_counter() + 60.0)
        except Exception as e:
            log_event(
                self.device_id or "-", "CONSOLE-EXEC", command,
                status="FAIL", error=str(e),
                duration_ms=round((time.perf_counter() - t0) * 1000),
            )
            await self.close()
            raise
        # output starts after the login dialog noise
        out = self.clean_command_output(self.buf[self._session_start:], send_command)
        await self.close()
        log_event(
            self.device_id or "-", "CONSOLE-EXEC", command, status="OK",
            duration_ms=round((time.perf_counter() - t0) * 1000),
        )
        return out

    async def run_scripted(
        self,
        command: str,
        answers: list[dict[str, str]] | None = None,
        timeout: float = 60.0,
    ) -> str:
        """Run one command and answer interactive prompts via rule list.

        answers: list of {"pattern": <regex>, "send": <text>}. While the
        device is mid-command, each read chunk is scanned (in order) against
        the patterns; on a match the matching reply text + CR is sent.
        Completion = a CLI prompt appears. Raises on timeout/connection error.
        Typical use: 'crypto key generate rsa' (answer modulus + confirm).
        """
        t0 = time.perf_counter()
        watches: list[tuple[re.Pattern, str]] = []
        for rule in answers or []:
            pattern = str(rule.get("pattern") or "")
            if not pattern:
                continue
            watches.append((re.compile(pattern, re.I), str(rule.get("send") or "\r")))
        try:
            await self.open()
            await self._recv_chunk(timeout=1.0)
            await asyncio.sleep(0.2)
            if self.pager_off_command:
                await self.send_line(self.pager_off_command)
                await self._drain_to_prompt(deadline=time.perf_counter() + 20.0)
                await asyncio.sleep(0.1)
            self._session_start = len(self.buf)
            send_command = self.command_without_paging(command)
            await self.send_line(send_command)
            deadline = time.perf_counter() + timeout
            while time.perf_counter() < deadline:
                await self._recv_chunk(timeout=0.5)
                window = self.buf[self._pos:]
                for rx, send in watches:
                    if rx.search(window):
                        self._pos = len(self.buf)
                        if send == "\r":
                            self.writer.write(b"\r")
                        else:
                            await self._type_slow(send)
                        try:
                            await self.writer.drain()
                        except Exception:
                            pass
                        break
                else:
                    if PROMPT_RE.search(window) or ROUTEROS_PROMPT_RE.search(window):
                        break
        except Exception as e:
            log_event(
                self.device_id or "-", "CONSOLE-SCRIPT", command,
                status="FAIL", error=str(e),
                duration_ms=round((time.perf_counter() - t0) * 1000),
            )
            await self.close()
            raise
        out = self.clean_command_output(self.buf[self._session_start:], send_command)
        await self.close()
        log_event(
            self.device_id or "-", "CONSOLE-SCRIPT", command, status="OK",
            duration_ms=round((time.perf_counter() - t0) * 1000),
        )
        return out

    async def _drain_to_prompt(self, deadline: float) -> None:
        """Keep reading, answering `--More--` / confirmations, until a final prompt."""
        while time.perf_counter() < deadline:
            try:
                event = await self.expect(timeout=15.0)
            except ConsoleTimeoutError:
                # best-effort: stop draining and let the caller clean/raise on
                # whatever was captured (e.g. `% Invalid input` in the buffer).
                return
            if event == "more":
                self._answer_more()
                continue
            if event == "prompt":
                return
            if event == "yesno":
                self._raw_send("n")  # decline (y/n) confirmations
                try:
                    asyncio.get_event_loop().create_task(self.writer.drain())
                except Exception:
                    pass
                continue
            if event == "confirm":
                self._raw_send("\r")
                continue
            # other dialog states should not appear during command output
            return

    def _answer_more(self) -> None:
        tail = self.buf[self._pos - 80 : self._pos].lower()
        self._raw_send("D" if "q quit" in tail and "d dump" in tail else " ")
        try:
            asyncio.get_event_loop().create_task(self.writer.drain())
        except Exception:
            pass

    async def run_config(self, lines: list[str]) -> str:
        """Run multiple configuration commands in one session (conf t ... end)."""
        if not lines:
            return ""
        t0 = time.perf_counter()
        try:
            await self.open()
            # enter config mode
            await self.send_line("configure terminal")
            await self._drain_to_prompt(deadline=time.perf_counter() + 20.0)
            for line in lines:
                await self.send_line(line)
                await self._drain_to_prompt(deadline=time.perf_counter() + 20.0)
            # exit config mode
            await self.send_line("end")
            await self._drain_to_prompt(deadline=time.perf_counter() + 20.0)
        except Exception as e:
            log_event(
                self.device_id or "-", "CONSOLE-CONFIG", "; ".join(lines),
                status="FAIL", error=str(e),
                duration_ms=round((time.perf_counter() - t0) * 1000),
            )
            await self.close()
            raise
        out = clean_cli_output(self.buf[self._session_start:], "configure terminal ...")
        await self.close()
        log_event(
            self.device_id or "-", "CONSOLE-CONFIG", "; ".join(lines), status="OK",
            duration_ms=round((time.perf_counter() - t0) * 1000),
        )
        return out
