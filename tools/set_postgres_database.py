"""Set the project database name without exposing or rewriting the DSN secret."""
from pathlib import Path


path = Path("backend/.env")
text = path.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)
for index, line in enumerate(lines):
    if line.startswith("POSTGRES_DSN="):
        value = line.rstrip("\r\n")
        if "/DATABASE" not in value:
            raise SystemExit("POSTGRES_DSN does not contain the expected placeholder")
        lines[index] = value.replace("/DATABASE", "/ainet_agent") + ("\r\n" if line.endswith("\r\n") else "\n")
        break
else:
    raise SystemExit("POSTGRES_DSN is missing")
path.write_text("".join(lines), encoding="utf-8")
print("postgres_dsn_database=ainet_agent")
