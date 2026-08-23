import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

prefix = "CISCO_IOSV_R1"
username = os.getenv(f"{prefix}_USERNAME", "admin")
password = os.getenv(f"{prefix}_PASSWORD", "Admin123!")
secret = os.getenv(f"{prefix}_SECRET", "Admin123!")

print(f"username: {username}")
print(f"password: {'*' * len(password) if password else 'None'}")
print(f"secret: {'*' * len(secret) if secret else 'None'}")

device = {
    "device_type": "cisco_ios",
    "host": "172.22.45.249",
    "username": username,
    "password": password,
    "secret": secret,
    "timeout": 30,
    "global_delay_factor": 2,
}

try:
    conn = ConnectHandler(**device)
    print("Connected!")
    print("Prompt:", conn.find_prompt())
    print("Check enable mode:", conn.check_enable_mode())
    if not conn.check_enable_mode():
        print("Entering enable mode...")
        conn.enable()
    print("After enable, prompt:", conn.find_prompt())
    print("In enable mode:", conn.check_enable_mode())
    output = conn.send_command("show version | include Version")
    print("Output:", output)
    conn.disconnect()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()