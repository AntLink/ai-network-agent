from pathlib import Path

# audit.py is at: backend/app/api/v1/endpoints/audit.py
audit_file = Path("C:/Users/mohfa/PycharmProjects/ai-network-agent/backend/app/api/v1/endpoints/audit.py")
logs_file = Path("C:/Users/mohfa/PycharmProjects/ai-network-agent/logs/audit.log")

print(f"audit.py: {audit_file.resolve()}")
print(f"logs: {logs_file.resolve()}")
print(f"exists: {logs_file.exists()}")
