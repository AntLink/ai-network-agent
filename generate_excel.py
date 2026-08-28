#!/usr/bin/env python3
"""
Generate Excel File dengan Informasi dari 3 Router
R1, R2 (Cisco), MT1 (MikroTik)
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ============================================================
# DATA ROUTER
# ============================================================

routers = [
    {
        "name": "R1",
        "type": "Cisco IOSv",
        "host": "172.22.134.144:2201",
        "username": "admin",
        "password": "admin",
        "hostname": "R1",
        "interfaces": [
            {"name": "GigabitEthernet0/0", "ip": "192.168.10.1", "subnet": "/24", "network": "192.168.10.0/24", "status": "up", "protocol": "up", "method": "manual"},
            {"name": "GigabitEthernet0/1", "ip": "10.10.12.1", "subnet": "/30", "network": "10.10.12.0/30", "status": "up", "protocol": "up", "method": "manual"},
            {"name": "GigabitEthernet0/2", "ip": "192.168.42.85", "subnet": "/24", "network": "192.168.42.0/24", "status": "up", "protocol": "up", "method": "DHCP"},
            {"name": "GigabitEthernet0/3", "ip": "10.10.13.1", "subnet": "/30", "network": "10.10.13.0/30", "status": "up", "protocol": "up", "method": "manual"},
            {"name": "NVI0", "ip": "192.168.10.1", "subnet": "/24", "network": "192.168.10.0/24", "status": "up", "protocol": "up", "method": "unset"},
        ],
        "static_routes": [
            {"destination": "0.0.0.0/0", "gateway": "192.168.42.1", "distance": "254", "description": "Default Gateway"},
            {"destination": "192.168.20.0/24", "gateway": "10.10.12.2", "distance": "1", "description": "Route ke R2 LAN"},
            {"destination": "192.168.30.0/24", "gateway": "10.10.13.2", "distance": "1", "description": "Route ke MT1 LAN"},
        ],
    },
    {
        "name": "R2",
        "type": "Cisco IOSv",
        "host": "172.22.134.144:2202",
        "username": "admin",
        "password": "admin",
        "hostname": "R2",
        "interfaces": [
            {"name": "GigabitEthernet0/0", "ip": "192.168.20.1", "subnet": "/24", "network": "192.168.20.0/24", "status": "up", "protocol": "up", "method": "NVRAM"},
            {"name": "GigabitEthernet0/1", "ip": "10.10.12.2", "subnet": "/30", "network": "10.10.12.0/30", "status": "up", "protocol": "up", "method": "NVRAM"},
            {"name": "GigabitEthernet0/2", "ip": "192.168.42.136", "subnet": "/24", "network": "192.168.42.0/24", "status": "up", "protocol": "up", "method": "DHCP"},
            {"name": "GigabitEthernet0/3", "ip": "unassigned", "subnet": "-", "network": "-", "status": "up", "protocol": "up", "method": "NVRAM"},
        ],
        "static_routes": [
            {"destination": "0.0.0.0/0", "gateway": "192.168.42.1", "distance": "254", "description": "Default Gateway"},
            {"destination": "192.168.10.0/24", "gateway": "10.10.12.1", "distance": "1", "description": "Route ke R1 LAN"},
            {"destination": "192.168.30.0/24", "gateway": "10.10.12.1", "distance": "1", "description": "Route ke MT1 (via R1)"},
        ],
    },
    {
        "name": "MT1",
        "type": "MikroTik RouterOS 7.22.1",
        "host": "172.22.134.144:2203",
        "username": "admin",
        "password": "admin",
        "hostname": "MikroTik",
        "interfaces": [
            {"name": "ether1", "ip": "10.10.13.2", "subnet": "/30", "network": "10.10.13.0/30", "status": "active", "protocol": "AS", "method": "static"},
            {"name": "ether2", "ip": "192.168.30.1", "subnet": "/24", "network": "192.168.30.0/24", "status": "active", "protocol": "AC", "method": "static"},
            {"name": "ether4", "ip": "192.168.42.52", "subnet": "/24", "network": "192.168.42.0/24", "status": "active", "protocol": "D", "method": "DHCP (Dynamic)"},
        ],
        "static_routes": [
            {"destination": "0.0.0.0/0", "gateway": "192.168.42.1", "distance": "1", "description": "Default Gateway (As+)"},
            {"destination": "10.10.12.0/30", "gateway": "10.10.13.1", "distance": "1", "description": "Route ke R1-R2 Link"},
            {"destination": "192.168.10.0/24", "gateway": "10.10.13.1", "distance": "1", "description": "Route ke R1 LAN"},
            {"destination": "192.168.20.0/24", "gateway": "10.10.13.1", "distance": "1", "description": "Route ke R2 LAN"},
        ],
    },
]


# ============================================================
# STYLES
# ============================================================

# Colors
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
SECTION_FILL = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
ALT_FILL = PatternFill(start_color="F2F7FB", end_color="F2F7FB", fill_type="solid")
GREEN_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
ORANGE_FILL = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
BLUE_FILL = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
WHITE_FILL = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

# Fonts
TITLE_FONT = Font(name="Calibri", size=18, bold=True, color="1F4E79")
SUBTITLE_FONT = Font(name="Calibri", size=12, bold=True, color="1F4E79")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
SECTION_FONT = Font(name="Calibri", size=12, bold=True, color="1F4E79")
BOLD_FONT = Font(name="Calibri", size=11, bold=True)
NORMAL_FONT = Font(name="Calibri", size=11)
MONO_FONT = Font(name="Consolas", size=10)

# Borders
thin_border = Border(
    left=Side(style="thin", color="B4C6E7"),
    right=Side(style="thin", color="B4C6E7"),
    top=Side(style="thin", color="B4C6E7"),
    bottom=Side(style="thin", color="B4C6E7")
)

# Alignment
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)


def set_header_style(ws, row, cols, header_fill=HEADER_FILL):
    """Apply header style to a row"""
    for col in range(1, cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = HEADER_FONT
        cell.fill = header_fill
        cell.alignment = CENTER
        cell.border = thin_border


def set_section_style(ws, row, cols):
    """Apply section header style"""
    for col in range(1, cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = SECTION_FONT
        cell.fill = SECTION_FILL
        cell.alignment = LEFT
        cell.border = thin_border


def auto_adjust_columns(ws, min_width=8, max_width=35):
    """Auto-adjust column widths"""
    for col in range(1, ws.max_column + 1):
        max_length = 0
        for row in range(1, ws.max_row + 1):
            cell = ws.cell(row=row, column=col)
            try:
                if cell.value:
                    length = len(str(cell.value))
                    if length > max_length:
                        max_length = length
            except:
                pass
        adjusted = max(min_width, min(max_width, max_length + 4))
        ws.column_dimensions[get_column_letter(col)].width = adjusted


def create_summary_sheet(wb):
    """Create Summary Sheet"""
    ws = wb.active
    ws.title = "Summary"
    
    # Title
    ws.merge_cells("A1:F1")
    ws["A1"] = "AI NETWORK AGENT - ROUTER TOPOLOGY REPORT"
    ws["A1"].font = TITLE_FONT
    ws["A1"].alignment = CENTER
    
    ws.merge_cells("A2:F2")
    ws["A2"] = "Static Routing Lab (GNS3) - 3 Router Topology"
    ws["A2"].font = SUBTITLE_FONT
    ws["A2"].alignment = CENTER
    ws["A2"].fill = YELLOW_FILL
    
    # Date
    from datetime import datetime
    ws.merge_cells("A3:F3")
    ws["A3"] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws["A3"].font = NORMAL_FONT
    ws["A3"].alignment = CENTER
    ws["A3"].fill = BLUE_FILL
    
    # Router Summary
    row = 5
    ws.merge_cells(f"A{row}:F{row}")
    ws[f"A{row}"] = "📊 ROUTER SUMMARY"
    ws[f"A{row}"].font = SECTION_FONT
    ws[f"A{row}"].fill = SECTION_FILL
    for col in range(1, 7):
        ws.cell(row=row, column=col).border = thin_border
        ws.cell(row=row, column=col).fill = SECTION_FILL
    row += 1
    
    # Headers
    headers = ["Device", "Type", "Host:Port", "Username", "Password", "Status"]
    for i, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=i, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER
        cell.border = thin_border
    row += 1
    
    # Data
    colors = [GREEN_FILL, GREEN_FILL, ORANGE_FILL]
    for router, color in zip(routers, colors):
        values = [
            router["name"],
            router["type"],
            router["host"],
            router["username"],
            router["password"],
            "Connected"
        ]
        for i, v in enumerate(values, 1):
            cell = ws.cell(row=row, column=i, value=v)
            cell.font = BOLD_FONT
            cell.alignment = CENTER
            cell.border = thin_border
            cell.fill = color
        row += 1
    
    # Topology overview
    row += 1
    ws.merge_cells(f"A{row}:F{row}")
    ws[f"A{row}"] = "🗺️ NETWORK TOPOLOGY"
    ws[f"A{row}"].font = SECTION_FONT
    ws[f"A{row}"].fill = SECTION_FILL
    for col in range(1, 7):
        ws.cell(row=row, column=col).border = thin_border
        ws.cell(row=row, column=col).fill = SECTION_FILL
    row += 1
    
    topology_data = [
        ("Network", "Subnet", "Connected To", "Gateway"),
        ("192.168.10.0/24", "R1 LAN", "R1 Gi0/0", "192.168.10.1 (R1)"),
        ("192.168.20.0/24", "R2 LAN", "R2 Gi0/0", "192.168.20.1 (R2)"),
        ("192.168.30.0/24", "MT1 LAN", "MT1 ether2", "192.168.30.1 (MT1)"),
        ("10.10.12.0/30", "R1-R2 Link", "R1 Gi0/1 <-> R2 Gi0/1", "-"),
        ("10.10.13.0/30", "R1-MT1 Link", "R1 Gi0/3 <-> MT1 ether1", "-"),
        ("192.168.42.0/24", "GNS3/DHCP", "Semua Router (WAN)", "192.168.42.1"),
    ]
    
    for data in topology_data:
        for i, v in enumerate(data, 1):
            cell = ws.cell(row=row, column=i, value=v)
            cell.font = NORMAL_FONT
            cell.alignment = LEFT if i > 1 else CENTER
            cell.border = thin_border
            cell.fill = WHITE_FILL
        row += 1
    
    # Connection summary
    row += 1
    ws.merge_cells(f"A{row}:F{row}")
    ws[f"A{row}"] = "🔗 CONNECTION DETAILS"
    ws[f"A{row}"].font = SECTION_FONT
    ws[f"A{row}"].fill = SECTION_FILL
    for col in range(1, 7):
        ws.cell(row=row, column=col).border = thin_border
        ws.cell(row=row, column=col).fill = SECTION_FILL
    row += 1
    
    connections = [
        ("From", "Interface", "To", "Interface", "Network", "Type"),
        ("R1", "Gi0/0", "PC1 / LAN", "-", "192.168.10.0/24", "LAN"),
        ("R1", "Gi0/1", "R2", "Gi0/1", "10.10.12.0/30", "Point-to-Point"),
        ("R1", "Gi0/2", "GNS3/NAT", "-", "192.168.42.0/24", "WAN (DHCP)"),
        ("R1", "Gi0/3", "MT1", "ether1", "10.10.13.0/30", "Point-to-Point"),
        ("R2", "Gi0/0", "PC2 / LAN", "-", "192.168.20.0/24", "LAN"),
        ("MT1", "ether2", "PC3 / LAN", "-", "192.168.30.0/24", "LAN"),
        ("MT1", "ether4", "GNS3/NAT", "-", "192.168.42.0/24", "WAN (DHCP)"),
    ]
    
    for data in connections:
        for i, v in enumerate(data, 1):
            cell = ws.cell(row=row, column=i, value=v)
            cell.font = NORMAL_FONT
            cell.alignment = CENTER if i <= 4 else LEFT
            cell.border = thin_border
            cell.fill = WHITE_FILL
        row += 1
    
    auto_adjust_columns(ws)
    return ws


def create_interface_sheet(wb):
    """Create Interface Report Sheet"""
    ws = wb.create_sheet("Interfaces")
    
    # Title
    ws.merge_cells("A1:H1")
    ws["A1"] = "INTERFACE IP ADDRESS REPORT"
    ws["A1"].font = TITLE_FONT
    ws["A1"].alignment = CENTER
    
    ws.merge_cells("A2:H2")
    ws["A2"] = "Semua IP Address Interfaces pada 3 Router"
    ws["A2"].font = SUBTITLE_FONT
    ws["A2"].alignment = CENTER
    ws["A2"].fill = YELLOW_FILL
    
    # Headers
    row = 4
    headers = ["Device", "Type", "Interface", "IP Address", "Subnet", "Network", "Status", "Protocol"]
    for i, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=i, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER
        cell.border = thin_border
    row += 1
    
    # Data - R1
    ws.merge_cells(f"A{row}:H{row}")
    ws[f"A{row}"] = "R1 (Cisco IOSv) - Host: 172.22.134.144:2201"
    ws[f"A{row}"].font = SECTION_FONT
    ws[f"A{row}"].fill = BLUE_FILL
    for col in range(1, 9):
        ws.cell(row=row, column=col).fill = BLUE_FILL
        ws.cell(row=row, column=col).border = thin_border
    row += 1
    
    for iface in routers[0]["interfaces"]:
        values = ["R1", "Cisco", iface["name"], iface["ip"], iface["subnet"], iface["network"], iface["status"], iface["protocol"]]
        for i, v in enumerate(values, 1):
            cell = ws.cell(row=row, column=i, value=v)
            cell.font = NORMAL_FONT
            cell.alignment = CENTER if i in [1, 2, 3, 4, 5, 7, 8] else LEFT
            cell.border = thin_border
            cell.fill = WHITE_FILL
        row += 1
    
    # Data - R2
    ws.merge_cells(f"A{row}:H{row}")
    ws[f"A{row}"] = "R2 (Cisco IOSv) - Host: 172.22.134.144:2202"
    ws[f"A{row}"].font = SECTION_FONT
    ws[f"A{row}"].fill = BLUE_FILL
    for col in range(1, 9):
        ws.cell(row=row, column=col).fill = BLUE_FILL
        ws.cell(row=row, column=col).border = thin_border
    row += 1
    
    for iface in routers[1]["interfaces"]:
        values = ["R2", "Cisco", iface["name"], iface["ip"], iface["subnet"], iface["network"], iface["status"], iface["protocol"]]
        for i, v in enumerate(values, 1):
            cell = ws.cell(row=row, column=i, value=v)
            cell.font = NORMAL_FONT
            cell.alignment = CENTER if i in [1, 2, 3, 4, 5, 7, 8] else LEFT
            cell.border = thin_border
            cell.fill = WHITE_FILL
        row += 1
    
    # Data - MT1
    ws.merge_cells(f"A{row}:H{row}")
    ws[f"A{row}"] = "MT1 (MikroTik RouterOS 7.22.1) - Host: 172.22.134.144:2203"
    ws[f"A{row}"].font = SECTION_FONT
    ws[f"A{row}"].fill = ORANGE_FILL
    for col in range(1, 9):
        ws.cell(row=row, column=col).fill = ORANGE_FILL
        ws.cell(row=row, column=col).border = thin_border
    row += 1
    
    for iface in routers[2]["interfaces"]:
        values = ["MT1", "MikroTik", iface["name"], iface["ip"], iface["subnet"], iface["network"], iface["status"], iface["protocol"]]
        for i, v in enumerate(values, 1):
            cell = ws.cell(row=row, column=i, value=v)
            cell.font = NORMAL_FONT
            cell.alignment = CENTER if i in [1, 2, 3, 4, 5, 7, 8] else LEFT
            cell.border = thin_border
            cell.fill = WHITE_FILL
        row += 1
    
    auto_adjust_columns(ws)
    return ws


def create_routes_sheet(wb):
    """Create Static Routes Sheet"""
    ws = wb.create_sheet("Static Routes")
    
    # Title
    ws.merge_cells("A1:F1")
    ws["A1"] = "STATIC ROUTING TABLE"
    ws["A1"].font = TITLE_FONT
    ws["A1"].alignment = CENTER
    
    ws.merge_cells("A2:F2")
    ws["A2"] = "Semua Static Routes pada 3 Router"
    ws["A2"].font = SUBTITLE_FONT
    ws["A2"].alignment = CENTER
    ws["A2"].fill = YELLOW_FILL
    
    # Headers
    row = 4
    headers = ["Device", "Type", "Destination", "Gateway", "Distance", "Description"]
    for i, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=i, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER
        cell.border = thin_border
    row += 1
    
    # Data per router
    for router in routers:
        color = BLUE_FILL if router["name"] in ["R1", "R2"] else ORANGE_FILL
        ws.merge_cells(f"A{row}:F{row}")
        ws[f"A{row}"] = f"{router['name']} ({router['type']})"
        ws[f"A{row}"].font = SECTION_FONT
        ws[f"A{row}"].fill = color
        for col in range(1, 7):
            ws.cell(row=row, column=col).fill = color
            ws.cell(row=row, column=col).border = thin_border
        row += 1
        
        for route in router["static_routes"]:
            values = [router["name"], router["type"], route["destination"], route["gateway"], route["distance"], route["description"]]
            for i, v in enumerate(values, 1):
                cell = ws.cell(row=row, column=i, value=v)
                cell.font = NORMAL_FONT
                cell.alignment = CENTER if i in [1, 2, 3, 4, 5] else LEFT
                cell.border = thin_border
                cell.fill = WHITE_FILL
            row += 1
    
    auto_adjust_columns(ws)
    return ws


def create_ping_sheet(wb):
    """Create Connectivity Test Sheet"""
    ws = wb.create_sheet("Connectivity Test")
    
    # Title
    ws.merge_cells("A1:D1")
    ws["A1"] = "CONNECTIVITY TEST MATRIX"
    ws["A1"].font = TITLE_FONT
    ws["A1"].alignment = CENTER
    
    # Headers
    row = 3
    headers = ["Source", "Destination", "Command", "Expected Result"]
    for i, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=i, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER
        cell.border = thin_border
    row += 1
    
    tests = [
        ("R1", "R2 (10.10.12.2)", "ping 10.10.12.2", "Success (R1 <-> R2 Link)"),
        ("R1", "MT1 (10.10.13.2)", "ping 10.10.13.2", "Success (R1 <-> MT1 Link)"),
        ("R1", "PC1 (192.168.10.x)", "ping 192.168.10.2", "Success (R1 LAN)"),
        ("R2", "R1 (10.10.12.1)", "ping 10.10.12.1", "Success (R2 <-> R1 Link)"),
        ("R2", "MT1 (10.10.12.1 via R1)", "ping 192.168.30.1", "Success (via R1)"),
        ("MT1", "R1 (10.10.13.1)", "ping 10.10.13.1", "Success (MT1 <-> R1 Link)"),
        ("MT1", "R2 LAN (192.168.20.1)", "ping 192.168.20.1", "Success (via R1)"),
        ("MT1", "R1 LAN (192.168.10.1)", "ping 192.168.10.1", "Success (via R1)"),
    ]
    
    for data in tests:
        for i, v in enumerate(data, 1):
            cell = ws.cell(row=row, column=i, value=v)
            cell.font = NORMAL_FONT
            cell.alignment = CENTER if i in [1, 2] else LEFT
            cell.border = thin_border
            cell.fill = WHITE_FILL
        row += 1
    
    auto_adjust_columns(ws, min_width=12)
    return ws


def create_login_sheet(wb):
    """Create SSH Login Info Sheet"""
    ws = wb.create_sheet("SSH Access")
    
    # Title
    ws.merge_cells("A1:E1")
    ws["A1"] = "SSH ACCESS INFORMATION"
    ws["A1"].font = TITLE_FONT
    ws["A1"].alignment = CENTER
    
    # Headers
    row = 3
    headers = ["Device", "Host", "Port", "Username", "Password"]
    for i, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=i, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER
        cell.border = thin_border
    row += 1
    
    # Data
    colors = [GREEN_FILL, GREEN_FILL, ORANGE_FILL]
    for router, color in zip(routers, colors):
        values = [
            router["name"],
            router["host"].split(":")[0],
            router["host"].split(":")[1],
            router["username"],
            router["password"]
        ]
        for i, v in enumerate(values, 1):
            cell = ws.cell(row=row, column=i, value=v)
            cell.font = BOLD_FONT
            cell.alignment = CENTER
            cell.border = thin_border
            cell.fill = color
        row += 1
    
    # SSH Commands
    row += 2
    ws.merge_cells(f"A{row}:E{row}")
    ws[f"A{row}"] = "SSH COMMANDS"
    ws[f"A{row}"].font = SECTION_FONT
    ws[f"A{row}"].fill = SECTION_FILL
    for col in range(1, 6):
        ws.cell(row=row, column=col).fill = SECTION_FILL
        ws.cell(row=row, column=col).border = thin_border
    row += 1
    
    ssh_commands = [
        ("R1", "ssh -p 2201 admin@172.22.134.144", "ssh -p 2201 admin@172.22.134.144"),
        ("R2", "ssh -p 2202 admin@172.22.134.144", "ssh -p 2202 admin@172.22.134.144"),
        ("MT1", "ssh -p 2203 admin@172.22.134.144", "ssh -p 2203 admin@172.22.134.144"),
    ]
    
    for data in ssh_commands:
        for i, v in enumerate(data, 1):
            cell = ws.cell(row=row, column=i, value=v)
            cell.font = MONO_FONT
            cell.alignment = LEFT
            cell.border = thin_border
            cell.fill = WHITE_FILL
        row += 1
    
    auto_adjust_columns(ws, min_width=15, max_width=45)
    return ws


def main():
    """Generate Excel file"""
    print("=" * 50)
    print("📊 Membuat Excel Report Router")
    print("=" * 50)
    
    wb = openpyxl.Workbook()
    
    # Create sheets
    create_summary_sheet(wb)
    create_interface_sheet(wb)
    create_routes_sheet(wb)
    create_ping_sheet(wb)
    create_login_sheet(wb)
    
    # Save file
    output_file = "router_topology_report.xlsx"
    wb.save(output_file)
    
    print(f"✅ Excel file created: {output_file}")
    print(f"   Location: {os.path.abspath(output_file)}")
    print(f"   Sheets: Summary, Interfaces, Static Routes, Connectivity Test, SSH Access")
    
    return output_file


if __name__ == "__main__":
    import os
    main()