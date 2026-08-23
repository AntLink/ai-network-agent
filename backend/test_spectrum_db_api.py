"""Smoke test: SpectrumDBClient end-to-end (SSH pull + decode)."""
import asyncio
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def main():
    from app.csms_monitor.spectrum_db import spectrum_db_client

    print("=== /measurements ===")
    ms = await spectrum_db_client.measurements(5)
    for m in ms:
        print(f"  id={m['measure_id']} task={m['task_id']} state={m['state']} {m['start']}")

    print("\n=== /latest ===")
    latest = await spectrum_db_client.latest_with_signal()
    for r in latest["results"]:
        print(f"  id={r['measure_id']} chan={r['first_chan']} max={r['max_level_dbm']} dBm "
              f"@bin {r['peak_bin']} t={r['timestamp']}")
        for pk in r["peaks"][:3]:
            print(f"      peak chan={pk['chan']} {pk['level_dbm']} dBm")

    mid = ms[0]["measure_id"] if ms else 5595
    print(f"\n=== /spectrum/{mid} ===")
    spec = await spectrum_db_client.spectrum(mid)
    print(f"  blocks: {len(spec['blocks'])}")
    if spec["blocks"]:
        b = spec["blocks"][0]
        print(f"  block[0]: first_chan={b['first_chan']} bins={b['bins']} peak={b['peak']}")
    print("\nOK - semua endpoint bekerja")


asyncio.run(main())
