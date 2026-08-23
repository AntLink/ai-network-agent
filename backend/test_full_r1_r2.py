"""Test lengkap CiscoIOSRouter di R1 & R2."""
import sys
sys.path.insert(0, ".")
from app.drivers.cisco import CiscoIOSRouter, Interface, StaticRoute

RESULTS = []

def step(name, desc, fn):
    try:
        out = fn()
        RESULTS.append((name, desc, "OK", out))
        print(f"[OK] {desc}")
    except Exception as e:
        RESULTS.append((name, desc, "GAGAL", f"{type(e).__name__}: {e}"))
        print(f"[XX] {desc} -> {type(e).__name__}: {e}")

for name, host in [("R1", "172.22.45.249"), ("R2", "172.22.36.184")]:
    print(f"\n========== {name} ({host}) ==========")
    r = CiscoIOSRouter(host=host, username="admin", password="Admin123!",
                       secret="Admin123!", device_id=f"cisco-iosv-{name.lower()}")

    step(name, "connect + enable", lambda: r._conn.connect())
    step(name, "get_interfaces", lambda: [f"{i.name}={i.ip_address}" for i in r.get_interfaces()])
    step(name, "get_hostname", lambda: r.get_hostname())
    step(name, "get_version", lambda: r.get_version()["version"][:60])
    step(name, "get_static_routes", lambda: [f"{x.destination}/{x.mask}->{x.next_hop}" for x in r.get_static_routes()])
    step(name, "set_interface (Loopback99)", lambda: r.set_interface(Interface(
        name="Loopback99", ip_address=f"199.9.9.{1 if name=='R1' else 2}",
        subnet_mask="255.255.255.255", description="driver-test", is_enabled=True)))
    step(name, "verifikasi Loopback99", lambda: f"{r.get_interface('Loopback99').name} up={r.get_interface('Loopback99').is_up}")
    step(name, "add_static_route", lambda: r.add_static_route(StaticRoute(
        destination=f"10.{1 if name=='R1' else 2}.0.0", mask="255.255.255.0", next_hop="192.168.200.2")))
    step(name, "get_static_routes (post)", lambda: len(r.get_static_routes()))
    step(name, "remove_static_route", lambda: r.remove_static_route(
        f"10.{1 if name=='R1' else 2}.0.0", "255.255.255.0", "192.168.200.2"))
    step(name, "delete_interface Loopback99", lambda: r.delete_interface("Loopback99"))
    step(name, "save_config", lambda: r.save_config())
    step(name, "disconnect", lambda: r._conn.disconnect())

print("\n===== REKAP =====")
ok = sum(1 for _, _, s, _ in RESULTS if s == "OK")
print(f"{ok}/{len(RESULTS)} langkah sukses")
fails = [(n, d, e) for n, d, s, e in RESULTS if s != "OK"]
for n, d, e in fails:
    print(f"  GAGAL [{n}] {d}: {e}")