import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient

from app.api.v1.endpoints.config import classify_commands
import app.api.v1.endpoints.config as config_endpoint
from app.api.v1.endpoints.gns3 import config_from_payload
from app.api.v1.endpoints.safety import is_read_like_request
from app.core.audit import redact_secrets
from app.core.config import settings
from app.drivers.cisco.parser import IOSParser
from app.drivers.mikrotik.driver import ros_kv, ros_value
from app.main import app


def test_policy_check_requires_approval_for_high_risk():
    client = TestClient(app)
    response = client.post(
        "/api/v1/policy/check",
        json={
            "device_id": "cisco-iosv-r1",
            "operation": "apply",
            "risk_level": "HIGH",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["requires_approval"] is True
    assert body["allowed"] is False


def test_policy_check_allows_low_risk_without_approval():
    client = TestClient(app)
    response = client.post(
        "/api/v1/policy/check",
        json={
            "device_id": "mikrotik-chr-mk-1",
            "operation": "read",
            "risk_level": "LOW",
        },
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is True


def test_device_detail_endpoint_returns_inventory_metadata():
    client = TestClient(app)
    response = client.get("/api/v1/devices/cisco-iosv-r1")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "cisco-iosv-r1"
    assert body["hostname"] == "R1"
    assert body["vendor"] == "cisco"
    assert body["management_address"]


def test_config_plan_can_be_created_listed_and_loaded(monkeypatch, tmp_path):
    monkeypatch.setattr(config_endpoint, "PLAN_FILE", tmp_path / "plans.json")
    monkeypatch.setattr(config_endpoint, "_plan_store", {})
    client = TestClient(app)
    create_response = client.post(
        "/api/v1/config/plan",
        json={
            "device_id": "cisco-iosv-r1",
            "commands": ["interface GigabitEthernet0/1", "description test"],
            "verify": [{"command": "show run interface GigabitEthernet0/1", "expect": "test"}],
            "save_on_success": False,
            "description": "non-live unit test",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["risk_level"] == "MEDIUM"

    list_response = client.get("/api/v1/config/plans")
    assert list_response.status_code == 200
    assert any(p["plan_id"] == created["plan_id"] for p in list_response.json()["plans"])

    get_response = client.get(f"/api/v1/config/plans/{created['plan_id']}")
    assert get_response.status_code == 200
    assert get_response.json()["description"] == "non-live unit test"


def test_config_plan_store_persists_to_file(monkeypatch, tmp_path):
    plan_file = tmp_path / "plans.json"
    monkeypatch.setattr(config_endpoint, "PLAN_FILE", plan_file)
    monkeypatch.setattr(
        config_endpoint,
        "_plan_store",
        {
            "abc12345": {
                "device_id": "cisco-iosv-r1",
                "commands": ["hostname R1"],
                "verify": [],
                "save_on_success": False,
                "description": "persist test",
                "risk_level": "MEDIUM",
                "status": "planned",
            }
        },
    )

    config_endpoint.persist_plan_store()

    loaded = config_endpoint.load_plan_store()
    assert loaded["abc12345"]["description"] == "persist test"


def test_config_risk_classification_flags_dangerous_commands():
    assert classify_commands(["interface Gi0/1", "description uplink"]) == "MEDIUM"
    assert classify_commands(["username ops secret test"]) == "HIGH"
    assert classify_commands(["reload"]) == "CRITICAL"


def test_routeros_value_quoting_preserves_free_text():
    assert ros_value("ether1") == "ether1"
    assert ros_value("WAN uplink") == '"WAN uplink"'
    assert ros_value('a"b') == '"a\\"b"'
    assert ros_kv("comment", "hello world") == 'comment="hello world"'


def test_audit_redacts_common_secret_arguments():
    text = "password=abc secret=def ipsec-secret=ghi wpa2-pre-shared-key=jkl"
    assert redact_secrets(text) == (
        "password=*** secret=*** ipsec-secret=*** wpa2-pre-shared-key=***"
    )


def test_gns3_flat_payload_extracts_config_only():
    cfg = config_from_payload(
        {
            "controller_url": "http://127.0.0.1:3080/v2",
            "username": "admin",
            "password": "pw",
            "name": "lab-a",
        }
    )
    assert cfg.controller_url == "http://127.0.0.1:3080/v2"
    assert cfg.username == "admin"
    assert cfg.password == "pw"
    assert not hasattr(cfg, "name")


def test_direct_write_guard_path_classification():
    assert is_read_like_request("GET", "/api/v1/cisco/cisco-iosv-r1/resources/version")
    assert is_read_like_request("POST", "/api/v1/gns3/projects")
    assert is_read_like_request("POST", "/api/v1/cisco/cisco-iosv-r1/tools/ping")
    assert not is_read_like_request("POST", "/api/v1/cisco/cisco-iosv-r1/system/hostname")
    assert not is_read_like_request("DELETE", "/api/v1/gns3/projects/project-1")


def test_direct_write_guard_blocks_write_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DIRECT_WRITE", False)
    client = TestClient(app)

    response = client.post(
        "/api/v1/cisco/cisco-iosv-r1/system/hostname",
        json={"name": "R1"},
    )

    assert response.status_code == 403
    assert "Direct write endpoints are disabled" in response.json()["detail"]


def test_cisco_running_config_parser_extracts_sections():
    raw = """
Building configuration...
!
version 15.6
hostname R1
!
username admin privilege 15 secret 5 hidden
!
interface GigabitEthernet0/0
 description MGMT
 ip address 172.22.45.249 255.255.240.0
 no shutdown
!
interface GigabitEthernet0/1.10
 encapsulation dot1Q 10
 ip address 192.168.10.1 255.255.255.0
!
vlan 10
 name USERS
!
router ospf 1
 router-id 1.1.1.1
 network 10.255.10.0 0.0.0.3 area 0
!
ip route 0.0.0.0 0.0.0.0 172.22.32.1
line vty 0 4
 login local
 transport input ssh
end
"""
    parsed = IOSParser.parse_running_config(raw)

    assert parsed["hostname"] == "R1"
    assert parsed["version"] == "15.6"
    assert parsed["users"][0]["username"] == "admin"
    assert parsed["interfaces"][0]["name"] == "GigabitEthernet0/0"
    assert parsed["interfaces"][0]["description"] == "MGMT"
    assert parsed["interfaces"][1]["encapsulation"] == "dot1Q 10"
    assert parsed["vlans"][0]["vlan_id"] == 10
    assert parsed["routing"]["protocols"][0]["name"] == "router ospf 1"
    assert parsed["routing"]["static_routes"] == ["ip route 0.0.0.0 0.0.0.0 172.22.32.1"]
    assert parsed["line_sections"][0]["name"] == "line vty 0 4"


def test_cisco_cpu_memory_parser_returns_ui_friendly_shape():
    cpu = """
CPU utilization for five seconds: 2%/0%; one minute: 3%; five minutes: 4%
 PID Runtime(ms)     Invoked      uSecs   5Sec   1Min   5Min TTY Process
   1          12          20        600  0.00%  0.00%  0.00%   0 Chunk Manager
"""
    memory = """
                Head    Total(b)     Used(b)     Free(b)   Lowest(b)  Largest(b)
Processor    CAAE880   322509696    64640180   257869516   252452416   251641220
I/O          8DAE880    63963136    52713804    11249332    11212064    11072572
"""

    parsed = IOSParser.parse_cpu_memory(cpu, memory)

    assert parsed["cpu"]["five_seconds"] == 2.0
    assert parsed["cpu"]["interrupt"] == 0.0
    assert parsed["cpu"]["one_minute"] == 3.0
    assert parsed["cpu"]["five_minutes"] == 4.0
    assert parsed["processes"][0]["pid"] == 1
    assert parsed["processes"][0]["process"] == "Chunk Manager"
    assert parsed["memory"]["pools"][0]["pool"] == "Processor"
    assert parsed["memory"]["summary"]["total_bytes"] == 386472832
    assert parsed["warnings"] == []
