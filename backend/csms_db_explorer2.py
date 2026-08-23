"""CSMS DB Explorer v2 - menemukan encoding level spektrum."""
import sqlite3
import struct
from datetime import datetime, timedelta

DB_PATH = r"csmsd_elf\csmsdb_copy.db"


def ole(v):
    try:
        return (datetime(1899, 12, 30) + timedelta(days=v)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(v)


def scan_levels(blob, label):
    n = len(blob)
    print(f"\n[{label}] len={n}")
    # float32 scan
    best = None
    for off in range(16, min(400, n - 4), 4):
        cnt = tot = 0
        mn, mx = 999.0, -999.0
        for i in range(off, n - 3, 4):
            v = struct.unpack_from("<f", blob, i)[0]
            tot += 1
            if -160 <= v <= 30:
                cnt += 1
                mn, mx = min(mn, v), max(mx, v)
        ratio = cnt / max(tot, 1)
        if best is None or ratio > best[1]:
            best = (off, ratio, cnt, mn, mx)
    print(f"  float32 best: off={best[0]} hit={best[1]*100:.0f}% ({best[2]}/{tot}) range={best[3]:.1f}..{best[4]:.1f}")
    # int16 scan
    best16 = None
    for off in range(16, min(200, n - 2), 2):
        cnt = tot = 0
        vals = []
        for i in range(off, n - 1, 2):
            v = struct.unpack_from("<h", blob, i)[0]
            tot += 1
            if -16000 <= v <= 3000:
                cnt += 1
                vals.append(v)
        ratio = cnt / max(tot, 1)
        if best16 is None or ratio > best16[1]:
            best16 = (off, ratio, cnt)
    print(f"  int16 best:   off={best16[0]} hit={best16[1]*100:.0f}%")
    return best


def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    print("=== SCHEDULE dengan tanggal OLE ===")
    cols = [r[1] for r in cur.execute("PRAGMA table_info(Schedule)")]
    for row in cur.execute(
        "SELECT MeasureId, TaskId, State, StartTime, StopTime, length(Msg) FROM Schedule ORDER BY StartTime DESC LIMIT 10"
    ):
        mid, tid, st, s, e, mlen = row
        print(f"  id={mid} task={tid} state={st} start={ole(s)} stop={ole(e)} msg={mlen}B")

    print("\n=== RESULTS per MeasureId terbaru ===")
    for row in cur.execute(
        "SELECT MeasureId, MsgSubType, FirstChan, COUNT(*) FROM Results "
        "WHERE MeasureId IN (SELECT DISTINCT MeasureId FROM Results ORDER BY MeasureId DESC LIMIT 3) "
        "GROUP BY MeasureId, MsgSubType, FirstChan ORDER BY MeasureId DESC, FirstChan LIMIT 25"
    ):
        print(f"  MeasureId={row[0]} sub={row[1]:#x} FirstChan={row[2]} rows={row[3]}")

    # ambil satu blob lengkap untuk analisis mendalam
    blob = cur.execute(
        "SELECT MsgBody FROM Results WHERE MsgSubType=65550 ORDER BY rowid DESC LIMIT 1"
    ).fetchone()[0]

    print("\n=== BLOB 65550 deep dive ===")
    print("first 96B as u32:")
    for i in range(0, 96, 16):
        vals = struct.unpack_from("<4I", blob, i)
        dbl = struct.unpack_from("<2d", blob, i)[0] if i + 16 <= len(blob) else 0
        print(f"  +{i:03d}: {' '.join(f'{v:>10}' for v in vals)}   | d0={dbl:.4f}" if abs(dbl) > 0.001 else f"  +{i:03d}: {' '.join(f'{v:>10}' for v in vals)}")

    print("\nu32 index 20..90:")
    for i in range(20, 92, 4):
        v = struct.unpack_from("<I", blob, i)[0]
        f = struct.unpack_from("<f", blob, i)[0]
        print(f"  +{i:03d}: u32={v:>12} f32={f:>14.4f}")

    print("\nlast 48B:", blob[-48:].hex())

    scan_levels(blob, "65550 full")

    # bandingkan dua blob berbeda FirstChan
    b1 = cur.execute(
        "SELECT MsgBody FROM Results WHERE MsgSubType=65550 AND FirstChan=42000 ORDER BY rowid DESC LIMIT 1"
    ).fetchone()[0]
    print("\nFirstChan=42000 vs 84000 diff pada 96B pertama:")
    a = b1[:96]
    b = blob[:96]
    diffs = [(i, a[i], b[i]) for i in range(96) if a[i] != b[i]]
    print(f"  byte diffs: {len(diffs)} -> posisi: {[d[0] for d in diffs[:30]]}")

    con.close()


if __name__ == "__main__":
    main()
