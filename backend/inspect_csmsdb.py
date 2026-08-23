import sqlite3

con = sqlite3.connect(r"csmsd_elf\csmsdb_copy.db")
cur = con.cursor()

print("=== TABLES ===")
tables = [n for (n,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
for n in tables:
    try:
        cnt = cur.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0]
        print(f"  {n}: {cnt} rows")
    except Exception as e:
        print(f"  {n}: ERR {e}")

print("\n=== Schedule sample (newest) ===")
try:
    for row in cur.execute(
        "SELECT MeasureId, TaskId, Priority, State, StartTime, StopTime, length(MsgBody) "
        "FROM Schedule ORDER BY MeasureId DESC LIMIT 8"
    ):
        print(" ", row)
except Exception as e:
    print("ERR", e)

print("\n=== Results sample (newest) ===")
try:
    for row in cur.execute(
        "SELECT MeasureId, MsgSubType, RunNumber, FirstChan, Az, El, length(MsgBody) "
        "FROM Results ORDER BY MeasureId DESC LIMIT 8"
    ):
        print(" ", row)
except Exception as e:
    print("ERR", e)

print("\n=== Results stats ===")
try:
    print(cur.execute("SELECT COUNT(*), MIN(MeasureId), MAX(MeasureId), AVG(length(MsgBody)) FROM Results").fetchone())
except Exception as e:
    print("ERR", e)

print("\n=== MsgBody blob preview (newest result) ===")
try:
    row = cur.execute("SELECT MsgSubType, MsgBody FROM Results ORDER BY rowid DESC LIMIT 1").fetchone()
    if row:
        subtype, blob = row
        print(f"subtype={subtype}, len={len(blob)}")
        print("first 64 bytes:", blob[:64].hex())
except Exception as e:
    print("ERR", e)
