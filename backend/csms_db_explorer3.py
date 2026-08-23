"""CSMS DB Explorer v3 - di mana data non-zero? + dekod task."""
import sqlite3
import struct
from datetime import datetime, timedelta

DB_PATH = r"csmsd_elf\csmsdb_copy.db"
OUT = open("csms_db_v3_out.txt", "w", encoding="utf-8")


def p(*a):
    s = " ".join(str(x) for x in a)
    OUT.write(s + "\n")
    print(s)


def ole(v):
    try:
        return (datetime(1899, 12, 30) + timedelta(days=v)).strftime("%y-%m-%d %H:%M")
    except Exception:
        return str(v)


def stats_f32(blob, off):
    n = (len(blob) - off) // 4
    if n <= 0:
        return None
    vals = struct.unpack_from(f"<{n}f", blob, off)
    nz = sum(1 for v in vals if v != 0.0)
    valid = [v for v in vals if -200 < v < 100]
    return {
        "bins": n,
        "nonzero": nz,
        "min": min(valid) if valid else None,
        "max": max(valid) if valid else None,
        "sample": sorted(set(round(v, 2) for v in valid))[:8],
    }


def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    p("=== SURVEI NON-ZERO: semua subtype x beberapa MeasureId ===")
    rows = cur.execute(
        "SELECT MeasureId, MsgSubType, FirstChan, MsgBody FROM Results "
        "ORDER BY MeasureId ASC LIMIT 400"
    ).fetchall()
    seen = {}
    for mid, st, fc, blob in rows:
        key = st
        info = stats_f32(blob, 88)
        if info and info["nonzero"] > 10:
            if key not in seen:
                seen[key] = (mid, fc, info)
    if seen:
        for st, (mid, fc, info) in seen.items():
            mn = f"{info['min']:.2f}" if info["min"] is not None else "?"
            mx = f"{info['max']:.2f}" if info["max"] is not None else "?"
            p(f"  subtype {st:#x}: PERTAMA non-zero di MeasureId={mid} FirstChan={fc}: "
              f"{info['nonzero']}/{info['bins']} bins, range {mn}..{mx}, contoh={info['sample']}")
    else:
        p("  TIDAK ADA data float32 non-signifikan pada 400 baris pertama (off=88)")

    # cek statistik nonzero per MeasureId untuk subtype dominan
    p("\n=== nonzero count per MeasureId (sub 0x1000e) ===")
    for mid, fc, blob in cur.execute(
        "SELECT MeasureId, FirstChan, MsgBody FROM Results WHERE MsgSubType=65550 ORDER BY rowid ASC LIMIT 12"
    ):
        info = stats_f32(blob, 88)
        mx = f"{info['max']:.2f}" if info["max"] is not None else "?"
        p(f"  id={mid} chan={fc}: nonzero={info['nonzero']}/{info['bins']} max={mx}")

    # bandingkan MeasureId lama vs baru
    p("\n=== MeasureId TERLAMA (5509) semua subtype ===")
    for st, blob in cur.execute(
        "SELECT MsgSubType, MsgBody FROM Results WHERE MeasureId=5509 LIMIT 4"
    ):
        info = stats_f32(blob, 88)
        mx = f"{info['max']:.2f}" if info["max"] is not None else "?"
        p(f"  sub={st:#x} len={len(blob)}: f32@88 nonzero={info['nonzero']}/{info['bins']} max={mx}")

    # dekod Schedule.Msg (task definition)
    p("\n=== Schedule.Msg (task def) - MeasureId 5547 ===")
    msg = cur.execute("SELECT Msg FROM Schedule WHERE MeasureId=5547").fetchone()[0]
    p(f"  len={len(msg)}")
    p(f"  head hexdump: {msg[:96].hex()}")
    u32 = struct.unpack_from("<24I", msg, 0)
    p(f"  u32[0..23]: {list(u32)}")
    dbl = struct.unpack_from("<3d", msg, 0)
    p(f"  d[0..2]: {dbl}")
    # cari string
    strs = []
    cur_str = b""
    for byte in msg:
        if 32 <= byte < 127:
            cur_str += bytes([byte])
        else:
            if len(cur_str) >= 4:
                strs.append(cur_str.decode())
            cur_str = b""
    p(f"  strings: {strs}")

    # ringkasan waktu
    p("\n=== cakupan waktu pengukuran ===")
    r = cur.execute("SELECT MIN(StartTime), MAX(StopTime) FROM Schedule").fetchone()
    p(f"  {ole(r[0])} s/d {ole(r[1])}")

    OUT.close()
    con.close()


if __name__ == "__main__":
    main()
