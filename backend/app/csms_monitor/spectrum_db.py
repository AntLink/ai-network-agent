import asyncio
import os
import sqlite3
import struct
import tempfile
from datetime import datetime, timedelta
from typing import List, Optional

import asyncssh

from app.csms_monitor.config import settings

OLE_EPOCH = datetime(1899, 12, 30)
HEADER_SIZE = 88
REMOTE_DB = "/media/tci/csms/data/csmsdb.db"
SUBTYPE_SPECTRUM = 0x1000E


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
        best_i, best_v = None, None
        for i, v in enumerate(self.levels):
            if v is not None and (best_v is None or v > best_v):
                best_i, best_v = i, v
        return best_i, best_v

    def peaks(self, top=5, floor=-110):
        lv = self.levels
        found = []
        for i in range(2, len(lv) - 2):
            v = lv[i]
            if v is not None and v > floor and v == max(x for x in lv[i - 2:i + 3] if x is not None):
                found.append({"bin": i, "level_dbm": round(v, 1),
                              "chan": self.first_chan + i})
        found.sort(key=lambda p: -p["level_dbm"])
        return found[:top]


def _decode_row(row) -> Optional[SpectrumRecord]:
    mid, st, run, fc, az, el, blob = row
    if not blob or len(blob) <= HEADER_SIZE:
        return None
    step = struct.unpack_from("<I", blob, 0)[0]
    ts = struct.unpack_from("<d", blob, 0x10)[0]
    n = (len(blob) - HEADER_SIZE) // 4
    raw = struct.unpack_from(f"<{n}f", blob, HEADER_SIZE)
    levels = [v if -200.0 < v < 100.0 else None for v in raw]
    return SpectrumRecord(mid, st, run, fc, az, el, ts, step, levels)


class SpectrumDBClient:
    """Menarik csmsdb.db dari CSMS device via SFTP, cache lokal, dekod spektrum."""

    def __init__(self):
        self._cache_path: Optional[str] = None
        self._cache_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
        self.ttl_seconds = int(os.getenv("CSMS_DB_TTL", "300"))

    async def _ensure_db(self, force=False) -> str:
        async with self._lock:
            fresh = (
                self._cache_path
                and self._cache_time
                and (datetime.now() - self._cache_time).total_seconds() < self.ttl_seconds
            )
            if fresh and not force:
                return self._cache_path

            tmp_local = os.path.join(tempfile.gettempdir(), "csmsdb_snap.db")
            async with asyncssh.connect(
                settings.CSMS_HOST,
                port=settings.CSMS_SSH_PORT,
                username=settings.CSMS_SSH_USER,
                password=settings.CSMS_SSH_PASS,
                known_hosts=None,
                connect_timeout=20,
            ) as conn:
                await asyncio.wait_for(
                    conn.run(
                        f"cp {REMOTE_DB} /tmp/csmsdb_snap.db && "
                        "gzip -c -f /tmp/csmsdb_snap.db > /tmp/csmsdb_snap.gz && sync; true"
                    ),
                    timeout=60,
                )
                gz_local = tmp_local + ".gz"
                async with conn.start_sftp_client() as sftp:
                    await asyncio.wait_for(
                        sftp.get("/tmp/csmsdb_snap.gz", gz_local),
                        timeout=180,
                    )
                import gzip as _gz
                with _gz.open(gz_local, "rb") as src, open(tmp_local, "wb") as dst:
                    dst.write(src.read())
                try:
                    os.remove(gz_local)
                except OSError:
                    pass

            old = self._cache_path
            self._cache_path = tmp_local
            self._cache_time = datetime.now()
            if old and old != tmp_local and os.path.exists(old):
                try:
                    os.remove(old)
                except OSError:
                    pass
            return self._cache_path

    async def measurements(self, limit=10) -> list:
        path = await self._ensure_db()
        con = sqlite3.connect(path)
        try:
            rows = con.execute(
                "SELECT MeasureId, TaskId, State, StartTime, StopTime FROM Schedule "
                "ORDER BY StartTime DESC LIMIT ?", (limit,)).fetchall()
            return [{
                "measure_id": r[0],
                "task_id": r[1],
                "state": r[2],
                "start": ole_to_dt(r[3]).isoformat(),
                "stop": ole_to_dt(r[4]).isoformat(),
            } for r in rows]
        finally:
            con.close()

    async def spectrum(self, measure_id: int, subtype: int = SUBTYPE_SPECTRUM) -> dict:
        path = await self._ensure_db()
        con = sqlite3.connect(path)
        try:
            rows = con.execute(
                "SELECT MeasureId, MsgSubType, RunNumber, FirstChan, Az, El, MsgBody "
                "FROM Results WHERE MeasureId=? AND MsgSubType=? ORDER BY FirstChan",
                (measure_id, subtype)).fetchall()
        finally:
            con.close()

        blocks = []
        for row in rows:
            rec = _decode_row(row)
            if not rec:
                continue
            idx, lvl = rec.peak()
            blocks.append({
                "first_chan": rec.first_chan,
                "timestamp": rec.dt.isoformat(),
                "bins": len(rec.levels),
                "levels": [round(v, 2) if v is not None else None for v in rec.levels],
                "peak": {"bin": idx, "chan": rec.first_chan + idx,
                         "level_dbm": round(lvl, 2)} if lvl is not None else None,
            })
        return {"measure_id": measure_id, "subtype": subtype, "blocks": blocks}

    async def latest_with_signal(self, subtype: int = SUBTYPE_SPECTRUM) -> dict:
        path = await self._ensure_db()
        con = sqlite3.connect(path)
        try:
            rows = con.execute(
                "SELECT MeasureId, MsgSubType, RunNumber, FirstChan, Az, El, MsgBody "
                "FROM Results WHERE MsgSubType=? ORDER BY rowid DESC LIMIT 400",
                (subtype,)).fetchall()
        finally:
            con.close()

        scored = []
        for row in rows:
            rec = _decode_row(row)
            if not rec:
                continue
            nz = [v for v in rec.levels if v is not None and v != 0.0]
            if len(nz) >= 50:
                scored.append((max(nz), rec))
        scored.sort(key=lambda x: -x[0])

        results = []
        for mx, rec in scored[:5]:
            idx, lvl = rec.peak()
            results.append({
                "measure_id": rec.measure_id,
                "first_chan": rec.first_chan,
                "timestamp": rec.dt.isoformat(),
                "max_level_dbm": round(mx, 2),
                "peak_bin": idx,
                "peaks": rec.peaks(),
            })
        return {"results": results}


spectrum_db_client = SpectrumDBClient()
