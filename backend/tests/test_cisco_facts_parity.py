import json
from pathlib import Path

from app.drivers.cisco.parser import IOSParser


def test_cisco_facts_matches_shared_semantic_vector():
    vector_path = Path(__file__).parents[2] / "docs" / "contracts" / "cisco-facts-vector.json"
    vector = json.loads(vector_path.read_text(encoding="utf-8"))
    parsed = IOSParser.parse_version(vector["raw"])
    actual = {
        "vendor": "cisco",
        "platform": "ios",
        "version": parsed.get("ios_version"),
        "uptime": parsed.get("uptime"),
        "image_file": parsed.get("image_file"),
    }
    hostname = next((line.split(" uptime is ", 1)[0].strip() for line in vector["raw"].splitlines() if " uptime is " in line), None)
    actual["hostname"] = hostname
    assert actual == vector["expected"]
