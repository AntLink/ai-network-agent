import os
import sys
sys.path.insert(0, ".")
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parent / ".env"
print(f"Loading .env from: {env_path}")
print(f"Exists: {env_path.exists()}")
load_dotenv(env_path)

print(f"LINUX_SERVER_USERNAME: {os.getenv('LINUX_SERVER_USERNAME')}")
print(f"LINUX_SERVER_PASSWORD: {os.getenv('LINUX_SERVER_PASSWORD')}")
