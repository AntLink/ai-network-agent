import json
import os
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def default_db_path() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "9router" / "db" / "data.sqlite"
    return Path.home() / ".9router" / "db" / "data.sqlite"


DB_PATH = Path(os.environ.get("NINEROUTER_DB", default_db_path()))

COMBOS = {
    "opencode-cheap": [
        "oc/laguna-s-2.1-free",
        "cf/@cf/zai-org/glm-4.7-flash",
        "mistral/codestral-latest",
    ],
    "opencode-coder": [
        "ocg/deepseek-v4-flash",
        "mistral/codestral-latest",
        "cx/gpt-5.4-mini",
        "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
    ],
    "opencode-reasoning": [
        "cx/gpt-5.4-mini",
        "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
        "cf/@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
        "cf/@cf/moonshotai/kimi-k2.5",
        "ocg/deepseek-v4-flash",
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"9Router database not found: {DB_PATH}")

    backup = DB_PATH.with_name(f"data.sqlite.backup-opencode-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(DB_PATH, backup)

    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        existing = {
            row[0]: row[1]
            for row in cur.execute("select name, id from combos").fetchall()
        }

        changed = []
        for name, models in COMBOS.items():
            payload = json.dumps(models, separators=(",", ":"))
            now = utc_now()
            if name in existing:
                cur.execute(
                    "update combos set models = ?, updatedAt = ? where name = ?",
                    (payload, now, name),
                )
                changed.append({"name": name, "action": "updated", "models": models})
            else:
                cur.execute(
                    "insert into combos (id, name, kind, models, createdAt, updatedAt) values (?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), name, None, payload, now, now),
                )
                changed.append({"name": name, "action": "inserted", "models": models})

        con.commit()
    finally:
        con.close()

    print(json.dumps({"database": str(DB_PATH), "backup": str(backup), "changed": changed}, indent=2))


if __name__ == "__main__":
    main()
