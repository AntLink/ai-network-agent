import re
import struct
import bisect
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

PORT_STRS = ["3302", "3303", "3304", "3305", "3306", "3307"]


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)

        secs = {}
        for sec in elf.iter_sections():
            if sec.header.sh_type == "SHT_NOBITS":
                continue
            secs[sec.name] = (sec.header.sh_addr, sec.data())

        funcs = []
        for name in ("SHT_SYMTAB", "SHT_DYNSYM"):
            pass
        syms = []
        for sec in elf.iter_sections():
            if sec.header.sh_type in ("SHT_SYMTAB", "SHT_DYNSYM"):
                for sym in sec.iter_symbols():
                    if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
                        syms.append((sym["st_value"], sym.name))
        syms = sorted(set(syms))
        starts = [a for a, _ in syms]

        def enclosing(addr):
            i = bisect.bisect_right(starts, addr) - 1
            return syms[i][1] if i >= 0 else "??"

        ro_addr, ro_data = secs.get(".rodata", (0, b""))

        # ---- 1) find port strings + context ---------------------------------
        print("=" * 78)
        print("  PORT STRING LOCATIONS + ROData CONTEXT")
        print("=" * 78)
        str_vas = {}
        for ps in PORT_STRS:
            pat = ps.encode() + b"\x00"
            idx = ro_data.find(pat)
            while idx != -1:
                # ensure standalone number (preceded by NUL)
                if idx == 0 or ro_data[idx - 1] == 0:
                    va = ro_addr + idx
                    str_vas.setdefault(ps, []).append(va)
                idx = ro_data.find(pat, idx + 1)

        for ps, vas in str_vas.items():
            print(f"\n--- '{ps}' at {[hex(v) for v in vas]} ---")
            for va in vas:
                off = va - ro_addr
                ctx = ro_data[max(0, off - 160): off + 64]
                parts = [p.decode("ascii", "replace") for p in ctx.split(b"\x00") if p]
                print(f"  @0x{va:08x} context strings: {parts[-8:]}")

        # ---- 2) xref pointers to these strings -------------------------------
        print("\n" + "=" * 78)
        print("  POINTER XREFS TO PORT STRINGS")
        print("=" * 78)
        ptr_secs = [".text", ".data", ".rodata"]
        for ps, vas in str_vas.items():
            for va in vas:
                pat = struct.pack("<I", va)
                for sname in ptr_secs:
                    if sname not in secs:
                        continue
                    sa, sd = secs[sname]
                    idx = sd.find(pat)
                    while idx != -1:
                        ref_va = sa + idx
                        if ref_va != va and idx % 4 == 0:
                            loc = f"<{enclosing(ref_va)}>" if sname == ".text" else sname
                            print(f"  '{ps}' referenced @ 0x{ref_va:08x} ({sname}) {loc}")
                        idx = sd.find(pat, idx + 1)

        # ---- 3) MOVW immediate encodings --------------------------------------
        print("\n" + "=" * 78)
        print("  MOVW IMMEDIATE HITS IN .text")
        print("=" * 78)
        ta, td = secs[".text"]
        for port in PORT_STRS:
            imm = int(port)
            imm4 = (imm >> 12) & 0xF
            imm12 = imm & 0xFFF
            # MOVW: cond 0011 0000 Rd imm4 imm12 -> we match fixed fields via regex on bytes
            cnt = 0
            for i in range(0, len(td) - 4, 2):
                w = struct.unpack_from("<I", td, i)[0]
                if (w & 0x0FF00000) == 0x03000000 and ((w >> 12) & 0xF) == imm4 and (w & 0xFFF) == imm12:
                    va = ta + i
                    print(f"  port {port}: MOVW @ 0x{va:08x} in <{enclosing(va)}>")
                    cnt += 1
                    if cnt >= 10:
                        break


if __name__ == "__main__":
    main()
