"""CSMS Spectrum Database Reader
Membaca hasil pengukuran spektrum dari database csmsd (SQLite) dan
mendekod MsgBody menjadi data siap pakai untuk backend.

Struktur blob Results (terdekod dari reverse engineering):
  Header 88 byte:
    +0x00 u32 step          (bandwidth/step, umumnya 10000)
    +0x08 u32 nbins         (jumlah bin, umumnya 244 -> lihat catatan)
    +0x10 f64 timestamp     (OLE/TDateTime)
    +0x20 f64 ?             (mis. 108.98)
    +0x2C u32 firstChan     (= kolom FirstChan, satuan channel TCI)
    +0x30 u32 ?             (mis. 4719)
  Offset 88: array float32[level] per bin (dBm utk sub 0x1000e)

Subtype yang dikenal:
  0x1000a (65546) occupancy/metric (%)   - body 9112B, 2256 bin
  0x1000b/c/e            spectrum levels - body 12056B, 2992 bin
"""
import sqlite3
import struct
import sys
from datetime import datetime, timedelta
from typing import List, Optional

OLE_EPOCH = datetime(1899, 12, 30)


def ole_to_dt(v: float) -> datetime:
    return OLE_EPOCH + timedelta(days=v)


class SpectrumRecord:
    __slots__ = ("measure_id", "subtype", "run", "first_chan", "az", "el",
                 "timestamp", "step", "levels")

    def __init__(self, measure_id, subtype, run, first_chan, az, el,
                 timestamp, step, levels):
        self.measure_id = measure_id
        self.subtype = subtype
        self.run = run
        self.first_chan = first_chan
        self.az = az
        self.el = el
        self.timestamp = timestamp
        self.step = step
        self.levels = levels

    @property
    def dt(self) -> datetime:
        return ole_to_dt(self.timestamp)

    def peak(self):
        """Return (index, level) bin tertinggi (abaikan sentinel)."""
        best_i, best_v = None, None
        for i, v in enumerate(self.levels):
            if v is not None and (best_v is None or v > best_v):
                best_i, best_v = i, v
        return best_i, best_v

    def __repr__(self):
        pk_i, pk_v = self.peak()
        return (f"<Spectrum id={self.measure_id} sub={self.subtype:#x} "
                f"chan={self.first_chan} t={self.dt:%m-%d %H:%M} "
                f"bins={len(self.levels)} peak=[{pk_i}]={pk_v:.1f}>")


HEADER_SIZE = 88


def decode_blob(measure_id, subtype, run, first_chan, az, el, blob) -> Optional[SpectrumRecord]:
    if len(blob) <= HEADER_SIZE:
        return None
    step = struct.unpack_from("<I", blob, 0)[0]
    ts = struct.unpack_from("<d", blob, 0x10)[0]
    n = (len(blob) - HEADER_SIZE) // 4
    raw = struct.unpack_from(f"<{n}f", blob, HEADER_SIZE)
    # sanitasi: buang sentinel/non-fisik (float32 max ~3.4e38, NaN)
    levels = [v if (-200.0 < v < 100.0) else None for v in raw]
    return SpectrumRecord(measure_id, subtype, run, first_chan, az, el,
                          ts, step, levels)


class CsmsDatabase:
    def __init__(self, path: str):
        self.con = sqlite3.connect(path)
        self.con.row_factory = sqlite3.Row

    def close(self):
        self.con.close()

    def latest_measurements(self, limit=10) -> list:
        rows = self.con.execute(
            "SELECT MeasureId, TaskId, State, StartTime, StopTime FROM Schedule "
            "ORDER BY StartTime DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            out.append({
                "measure_id": r["MeasureId"],
                "task_id": r["TaskId"],
                "state": r["State"],
                "start": ole_to_dt(r["StartTime"]),
                "stop": ole_to_dt(r["StopTime"]),
            })
        return out

    def spectrum_for_measurement(self, measure_id: int,
                                 subtype: int = 0x1000E) -> List[SpectrumRecord]:
        rows = self.con.execute(
            "SELECT MeasureId, MsgSubType, RunNumber, FirstChan, Az, El, MsgBody "
            "FROM Results WHERE MeasureId=? AND MsgSubType=? ORDER BY FirstChan",
            (measure_id, subtype)).fetchall()
        recs = []
        for r in rows:
            rec = decode_blob(r["MeasureId"], r["MsgSubType"], r["RunNumber"],
                              r["FirstChan"], r["Az"], r["El"], r["MsgBody"])
            if rec:
                recs.append(rec)
        return recs

    def latest_with_signal(self, subtype: int = 0x1000E,
                           min_bins_active=50) -> List[SpectrumRecord]:
        """Cari record dengan sinyal nyata (bin non-zero), urut level tertinggi."""
        rows = self.con.execute(
            "SELECT MeasureId, MsgSubType, RunNumber, FirstChan, Az, El, MsgBody "
            "FROM Results WHERE MsgSubType=? ORDER BY rowid DESC LIMIT 400",
            (subtype,)).fetchall()
        scored = []
        for r in rows:
            rec = decode_blob(r["MeasureId"], r["MsgSubType"], r["RunNumber"],
                              r["FirstChan"], r["Az"], r["El"], r["MsgBody"])
            if not rec:
                continue
            nz = [v for v in rec.levels if v is not None and v != 0.0]
            if len(nz) >= min_bins_active:
                scored.append((max(nz), len(nz), rec))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        return [rec for _, _, rec in scored[:5]]


def demo():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    db = CsmsDatabase(r"csmsd_elf\csmsdb_copy.db")

    print("=== Pengukuran terakhir ===")
    for m in db.latest_measurements(5):
        print(f"  id={m['measure_id']} task={m['task_id']} state={m['state']} "
              f"{m['start']:%d-%b %H:%M} .. {m['stop']:%d-%b %H:%M}")

    print("\n=== Sweep dengan sinyal terkuat (sub 0x1000E) ===")
    for rec in db.latest_with_signal():
        idx, lvl = rec.peak()
        nz = sum(1 for v in rec.levels if v is not None and v != 0.0)
        print(f"  {rec}  nonzero={nz} bins")

        # tampilkan top-5 puncak lokal sederhana
        peaks = []
        lv = rec.levels
        for i in range(2, len(lv) - 2):
            v = lv[i]
            if v is not None and v > -110 and v == max(x for x in lv[i - 2:i + 3] if x is not None):
                peaks.append((i, round(v, 1)))
        peaks.sort(key=lambda x: -x[1])
        for i, v in peaks[:5]:
            print(f"      bin {i}: {v} dBm  (chan≈{rec.first_chan + i})")

    db.close()


if __name__ == "__main__":
    demo()
