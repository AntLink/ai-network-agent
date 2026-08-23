"""Test CiscoIOSRouter driver di R2 (priv 15)."""
import sys
sys.path.insert(0, ".")
from app.drivers.cisco import CiscoIOSRouter, Interface, StaticRoute

r = CiscoIOSRouter(
    host="172.22.36.184",
    username="admin",
    password="Admin123!",
    secret="Admin123!",
    device_id="cisco-iosv-r2",
)

print("[1] connect + get_interfaces")
try:
    r._conn.connect()
    intfs = r.get_interfaces()
    for i in intfs:
        print(f"    {i.name:<22} {str(i.ip_address):<16} {'UP' if i.is_up else 'down'}")
except Exception as e:
    print(f"    GAGAL: {type(e).__name__}: {e}")
    sys.exit(1)

print("\n[2] get_hostname")
try:
    print("   ", r.get_hostname())
except Exception as e:
    print(f"    GAGAL: {type(e).__name__}: {e}")

print("\n[3] get_version")
try:
    v = r.get_version()
    print("   ", v["version"][:80])
except Exception as e:
    print(f"    GAGAL: {type(e).__name__}: {e}")

print("\n[4] set_interface description-only test (Loopback99)")
try:
    out = r.set_interface(Interface(
        name="Loopback99",
        ip_address="199.99.99.1",
        subnet_mask="255.255.255.255",
        description="test-driver-api",
        is_enabled=True,
    ))
    print("    OK - Loopback99 dibuat")
except Exception as e:
    print(f"    GAGAL: {type(e).__name__}: {e}")

print("\n[5] verifikasi Loopback99 ada")
try:
    lo = r.get_interface("Loopback99")
    print(f"    {lo.name} {lo.ip_address} up={lo.is_up}" if lo else "    TIDAK KETEMU")
except Exception as e:
    print(f"    GAGAL: {type(e).__name__}: {e}")

print("\n[6] add_static_route test")
try:
    out = r.add_static_route(StaticRoute(
        destination="10.99.0.0", mask="255.255.255.0", next_hop="192.168.200.2"))
    print("    OK")
except Exception as e:
    print(f"    GAGAL: {type(e).__name__}: {e}")

print("\n[7] get_static_routes")
try:
    routes = r.get_static_routes()
    if not routes:
        print("    (TextFSM tidak match / tidak ada static route)")
    for rt in routes:
        print(f"    {rt.destination}/{rt.mask} -> {rt.next_hop}")
except Exception as e:
    print(f"    GAGAL: {type(e).__name__}: {e}")

print("\n[8] cleanup (hapus loopback & route test)")
try:
    r.remove_static_route("10.99.0.0", "255.255.255.0", "192.168.200.2")
    r.delete_interface("Loopback99")
    print("    OK")
except Exception as e:
    print(f"    GAGAL: {type(e).__name__}: {e}")

print("\n[9] save_config")
try:
    out = r.save_config()
    print("    OK:", [l.strip() for l in out.splitlines() if l.strip()][-1])
except Exception as e:
    print(f"    GAGAL: {type(e).__name__}: {e}")

r._conn.disconnect()
print("\n=== SELESAI ===")