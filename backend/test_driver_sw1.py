import sys, os
sys.path.insert(0, ".")
from dotenv import load_dotenv; load_dotenv()
from app.drivers.cisco import CiscoIOSRouter

r = CiscoIOSRouter(host="172.22.38.10",
                   username=os.getenv("CISCO_IOSVL2_SW1_USERNAME"),
                   password=os.getenv("CISCO_IOSVL2_SW1_PASSWORD"),
                   secret=os.getenv("CISCO_IOSVL2_SW1_SECRET"),
                   device_id="cisco-iosvl2-sw1")
r._conn.connect()
print("hostname :", r.get_hostname())
print("version  :", r.get_version()["version"][:70])
for i in r.get_interfaces():
    status = "UP" if i.is_up else "down"
    print(i.name.ljust(12), str(i.ip_address).ljust(16), status)
r._conn.disconnect()
print("=== DRIVER OK DI SW1 ===")