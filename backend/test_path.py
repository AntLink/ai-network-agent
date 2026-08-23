from pathlib import Path
print(f"audit.py location: {Path(__file__).resolve()}")
print(f"logs path: {Path(__file__).resolve().parent.parent.parent.parent.parent / 'logs' / 'audit.log'}")
print(f"exists: {(Path(__file__).resolve().parent.parent.parent.parent.parent / 'logs' / 'audit.log').exists()}")
