import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

prefix = "CISCO_IOSV_R1"
username = os.getenv(f"{prefix}_USERNAME", "admin")
password = os.getenv(f"{prefix}_PASSWORD", "Admin123!")

device = {
    "device_type": "cisco_ios",
    "host": "172.22.45.249",
    "username": username,
    "password": password,
    # no secret
    "timeout": 30,
    "global_delay_factor": 2,
}

try:
    conn = ConnectHandler(**device)
    print("Connected!")
    print("Prompt:", conn.find_prompt())
    print("Check enable mode:", conn.check_enable_mode())
    output = conn.send_command("show version | include Version")
    print("Output:", output)
    conn.disconnect()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()