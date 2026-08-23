"""Test ulang get_static_routes di R2 & R1."""
import sys
sys.path.insert(0, ".")
from app.drivers.cisco import CiscoIOSRouter

for name, host, secret in [("R2", "172.22.36.184", "Admin123!"),
                           ("R1", "172.22.45.249", None)]:
    print(f"===== {name} ({host}) =====")
    r = CiscoIOSRouter(host=host, username="admin", password="Admin123!",
                       secret=secret or "Admin123!", device_id=f"cisco-iosv-{name.lower()}")
    try:
        r._conn.connect()
        routes = r.get_static_routes()
        if not routes:
            print("    (tidak ada static route)")
        for rt in routes:
            print(f"    {rt.destination} {rt.mask} -> {rt.next_hop}")
        # interface juga sekalian
        intfs = r.get_interfaces()
        up = sum(1 for i in intfs if i.is_up)
        print(f"    interfaces: {len(intfs)} total, {up} up")
    except Exception as e:
        print(f"    GAGAL: {type(e).__name__}: {e}")
    finally:
        r._conn.disconnect()
    print()