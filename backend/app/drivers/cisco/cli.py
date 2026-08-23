"""Cisco IOS CLI session logic.

Prompt detection, output cleaning and error parsing live here (driver layer),
NOT in the SSH transport, so the transport stays vendor-neutral.
"""
import re

from app.transports.ssh import SSHTransport, PromptTimeoutError

PROMPT_RE = re.compile(r"(?m)^[^\r\n]+(?:\(config[^)]*\))?[#>]\s*$")

CONFIRM_RE = re.compile(r"(\?|\[confirm\])\s*$")

IOS_ERROR_RE = re.compile(
    r"(?im)^% ?("
    r"Invalid input|"
    r"Incomplete command|"
    r"Ambiguous command|"
    r"Unrecognized command|"
    r"Unknown command|"
    r"Error|"
    r"Failed|"
    r"Cannot|"
    r"Not enough|"
    r"Bad"
    r")"
)


class CiscoCLIError(Exception):
    """Cisco CLI command failed with % error."""
    pass


async def drain_prompt(reader, max_wait: float = 5.0) -> str:
    buf = ""
    import time

    started = time.perf_counter()
    while time.perf_counter() - started < max_wait:
        try:
            piece = await reader.read(4096)
        except Exception:
            break
        if not piece:
            break
        if isinstance(piece, bytes):
            piece = piece.decode("utf-8", errors="replace")
        buf += piece
        if PROMPT_RE.search(buf) or CONFIRM_RE.search(buf.rstrip()):
            break
    return buf


def clean_cli_output(raw: str, command: str | None = None) -> str:
    """Strip \r, blank edges, command echo and trailing prompt."""
    raw = raw.replace("\r", "")
    lines = raw.splitlines()

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    if command and lines:
        first = lines[0].strip()
        if first == command.strip():
            lines.pop(0)
        elif first.endswith(command.strip()):
            lines.pop(0)

    while lines and PROMPT_RE.fullmatch(lines[-1].strip()):
        lines.pop()

    return "\n".join(lines).strip()


def raise_for_ios_error(output: str, command: str) -> None:
    """Raise CiscoCLIError only for actual IOS CLI errors (%...), never banners/warnings."""
    if not IOS_ERROR_RE.search(output):
        return

    error_lines = [
        line
        for line in output.splitlines()
        if line.lstrip().startswith("%") or line.strip() == "^"
    ]
    detail = "\n".join(error_lines).strip() or output.strip()
    raise CiscoCLIError(f"Cisco IOS command failed: {command}\n{detail}")


async def run_batch(transport: SSHTransport, commands: list[str]) -> list[str]:
    """Run multiple EXEC commands in ONE interactive login.

    Banner/prompt discarded; echo stripped; per-command IOS error check.
    """
    if not commands:
        return []

    async def _do() -> list[str]:
        outputs: list[str] = []
        async with transport.interactive() as proc:
            await drain_prompt(proc.stdout, max_wait=4.0)

            proc.stdin.write("terminal length 0\n")
            cleaned = clean_cli_output(await drain_prompt(proc.stdout), "terminal length 0")
            raise_for_ios_error(cleaned, "terminal length 0")

            for command in commands:
                proc.stdin.write(command + "\n")
                cleaned = clean_cli_output(await drain_prompt(proc.stdout), command)
                raise_for_ios_error(cleaned, command)
                outputs.append(cleaned)
        return outputs

    return await transport._with_deadline(_do(), f"batch of {len(commands)} command(s)")


async def run_config_lines(transport: SSHTransport, lines: list[str]) -> str:
    """Run configuration commands inside `conf t ... end` in one login."""

    if not lines:
        return ""

    async def _do() -> str:
        outputs: list[str] = []
        async with transport.interactive() as proc:
            await drain_prompt(proc.stdout, max_wait=4.0)

            for send_line, expect_echo in [
                ("terminal length 0", "terminal length 0"),
                ("configure terminal", "configure terminal"),
                *[(line, line) for line in lines],
                ("end", "end"),
            ]:
                proc.stdin.write(send_line + "\n")
                cleaned = clean_cli_output(await drain_prompt(proc.stdout), expect_echo)
                raise_for_ios_error(cleaned, send_line)
                if cleaned and send_line not in ("terminal length 0", "configure terminal", "end"):
                    outputs.append(cleaned)
        return "\n".join(outputs).strip()

    return await transport._with_deadline(_do(), "; ".join(lines))


async def send_interactive(
    transport: SSHTransport,
    command: str,
    max_wait: float = 15.0,
    confirms: int = 4,
) -> str:
    """Kirim satu perintah interaktif; jawab semua prompt konfirmasi
    (mis. 'Destination filename ...?' / '[confirm]') sampai kembali ke prompt CLI."""
    async with transport.interactive() as proc:
        await drain_prompt(proc.stdout, max_wait=4.0)
        proc.stdin.write(command + "\n")
        full = ""
        for _ in range(confirms + 1):
            out = await drain_prompt(proc.stdout, max_wait=max_wait)
            full += out
            stripped = out.rstrip()
            if CONFIRM_RE.search(stripped) and not PROMPT_RE.search(stripped):
                proc.stdin.write("\n")  # terima default
                continue
            if PROMPT_RE.search(full):
                break
        return full