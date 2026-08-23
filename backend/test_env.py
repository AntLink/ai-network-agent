import os
import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

print(f"LINUX_SERVER_USERNAME: {os.getenv('LINUX_SERVER_USERNAME')}")
print(f"LINUX_SERVER_PASSWORD: {os.getenv('LINUX_SERVER_PASSWORD')}")
print(f"NETWORK_USERNAME: {os.getenv('NETWORK_USERNAME')}")
print(f"NETWORK_PASSWORD: {os.getenv('NETWORK_PASSWORD')}")

# Test the prefix logic
device_id = "linux-server"
prefix = device_id.upper().replace("-", "_")
print(f"Prefix: {prefix}")
print(f"{prefix}_USERNAME: {os.getenv(f'{prefix}_USERNAME')}")
print(f"{prefix}_PASSWORD: {os.getenv(f'{prefix}_PASSWORD')}")
