from app.services.terminal_service import terminal_session_manager


def test_parse_cisco_suggestions():
    raw = """
show ip ?
  interface     IP interface status and configuration
  route         IP routing table
  ospf          OSPF information
R1#
"""

    suggestions = terminal_session_manager._parse_suggestions(raw, "show ip ", "cisco")

    assert {"value": "interface", "description": "IP interface status and configuration"} in suggestions
    assert {"value": "route", "description": "IP routing table"} in suggestions
    assert all(item["value"] != "R1#" for item in suggestions)


def test_parse_mikrotik_suggestions():
    raw = """
[admin@MK-1] > /ip 
address  arp  cloud  dhcp-client  dns  firewall  route  service
[admin@MK-1] >
"""

    suggestions = terminal_session_manager._parse_suggestions(raw, "/ip ", "mikrotik")

    assert suggestions[0]["value"] == "address"
    assert {"value": "route", "description": ""} in suggestions


def test_normalize_mikrotik_probe_adds_root_slash_and_space():
    assert terminal_session_manager._normalize_probe("ip", "mikrotik") == "/ip "
    assert terminal_session_manager._normalize_probe("/ip", "mikrotik") == "/ip "
    assert terminal_session_manager._normalize_probe("ip firewall", "mikrotik") == "/ip firewall "


def test_normalize_cisco_probe_preserves_help_space():
    assert terminal_session_manager._normalize_probe("show ip ?", "cisco") == "show ip "
    assert terminal_session_manager._normalize_probe("show ?", "cisco") == "show "


def test_parse_cisco_suggestions_not_limited_to_short_lists():
    raw = "\n".join([f"  cmd{i}  Description {i}" for i in range(220)])
    raw += "\n  xsd-format  Show the ODM XSD for the command"

    suggestions = terminal_session_manager._parse_suggestions(raw, "show ?", "cisco")

    assert len(suggestions) == 221
    assert suggestions[-1] == {"value": "xsd-format", "description": "Show the ODM XSD for the command"}
