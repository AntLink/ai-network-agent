"""CSMS Database Explorer & Spectrum Decoder
Menganalisis struktur csmsdb.db dan mendekod MsgBody menjadi data spektrum.
"""
import sqlite3
import struct
import sys
from collections import Counter

DB_PATH = r"csmsd_elf\csmsdb_copy.db"


def hexdump(b, limit=48):
    return " ".join(f"{x:02x}" for x in b[:limit])


def explore_blob(blob):
    """Coba beberapa interpretasi header blob."""
    info = {}
    n = len(blob)
    info["len"] = n
    # u32 stream pertama
    u32s = struct.unpack_from("<8I", blob, 0)
    info["u32_first8"] = list(u32s)
    u16s = struct.unpack_from("<12H", blob, 0)
    info["u16_first12"] = list(u16s)
    # cari offset mulai deretan float64 valid (-200..50 dBm)
    best_off, best_cnt = None, 0
    for off in range(8, min(128, n - 8), 4):
        cnt = 0
        for i in range(off, min(n - 7, off + 512), 8):
            v = struct.unpack_from("<d", blob, i)[0]
            if -200.0 <= v <= 50.0:
                cnt += 1
        if cnt > best_cnt:
            best_cnt, best_off = cnt, off
    info["f64_start"] = best_off
    info["f64_count_dbm_like"] = best_cnt
    total_doubles = (n - best_off) // 8 if best_off else 0
    info["f64_total_slots"] = total_doubles
    vals = []
    if best_off:
        for i in range(best_off, best_off + min(total_doubles, 400) * 8, 8):
            v = struct.unpack_from("<d", blob, i)[0]
            if -200.0 <= v <= 50.0:
                vals.append(round(v, 2))
    info["nonzero_vals_sample"] = [v for v in vals if v != 0.0][:12]
    info["min_val"] = min(vals) if vals else None
    info["max_val"] = max(vals) if vals else None
    return info


def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    print("=" * 78)
    print("  CSMS DATABASE EXPLORER")
    print("=" * 78)

    # ---- schema -------------------------------------------------------------
    print("\n--- SCHEMA ---")
    for (sql,) in cur.execute("SELECT sql FROM sqlite_master WHERE type='table'"):
        print(" ", sql.replace("\n", " ") if sql else sql)

    # ---- distribusi ---------------------------------------------------------
    print("\n--- RESULTS: distribusi MsgSubType ---")
    for st, cnt, avg_len, mn_id, mx_id in cur.execute(
        "SELECT MsgSubType, COUNT(*), AVG(length(MsgBody)), MIN(MeasureId), MAX(MeasureId) "
        "FROM Results GROUP BY MsgSubType ORDER BY COUNT(*) DESC"
    ):
        print(f"  subtype={st} ({st:#x}): {cnt} rows, avg body={avg_len:.0f}B, MeasureId {mn_id}..{mx_id}")

    print("\n--- Schedule: semua task ---")
    try:
        cols = [r[1] for r in cur.execute("PRAGMA table_info(Schedule)")]
        print("  columns:", cols)
        for row in cur.execute("SELECT * FROM Schedule LIMIT 20"):
            show = []
            for c, v in zip(cols, row):
                if isinstance(v, bytes):
                    show.append(f"{c}=<blob {len(v)}B>")
                else:
                    show.append(f"{c}={v}")
            print("   ", " ".join(show))
    except Exception as e:
        print("ERR", e)

    # ---- analisis blob per subtype ------------------------------------------
    print("\n--- BLOB STRUCTURE ANALYSIS (per subtype, sampel terbaru) ---")
    subtypes = [r[0] for r in cur.execute("SELECT DISTINCT MsgSubType FROM Results")]
    decoders = {}
    for st in subtypes:
        row = cur.execute(
            "SELECT MsgBody FROM Results WHERE MsgSubType=? ORDER BY rowid DESC LIMIT 1", (st,)
        ).fetchone()
        if not row:
            continue
        info = explore_blob(row[0])
        decoders[st] = info
        print(f"\n  subtype {st} ({st:#x}):")
        for k, v in info.items():
            print(f"    {k}: {v}")
        print(f"    head hex: {hexdump(row[0])}")

    # ---- decode sweep terbaru untuk subtype dominan -------------------------
    print("\n" + "=" * 78)
    print("  DECODED SPECTRUM SWEEP (subtype terbanyak)")
    print("=" * 78)
    dom_st = Counter({st: c for st, c, *_ in cur.execute(
        "SELECT MsgSubType, COUNT(*) FROM Results GROUP BY MsgSubType")}).most_common(1)[0][0]
    rows = cur.execute(
        "SELECT MeasureId, FirstChan, Az, El, MsgBody FROM Results "
        "WHERE MsgSubType=? ORDER BY rowid DESC LIMIT 5", (dom_st,)
    ).fetchall()
    info = decoders.get(dom_st, {})
    off = info.get("f64_start") or 16
    for mid, chan, az, el, blob in rows:
        n_double = (len(blob) - off) // 8
        levels = struct.unpack_from(f"<{n_double}d", blob, off)
        valid = [v for v in levels if -200 <= v <= 50]
        print(f"\n  MeasureId={mid} FirstChan={chan} Az={az} El={el} bins={n_double}")
        if valid:
            print(f"    level range: {min(valid):.1f} .. {max(valid):.1f} dBm")
            nz = [(i, round(v, 1)) for i, v in enumerate(levels) if -200 <= v <= 50 and v != 0]
            print(f"    bin non-zero: {len(nz)}; contoh: {nz[:10]}")

    con.close()
    print("\nDONE")


if __name__ == "__main__":
    main()
