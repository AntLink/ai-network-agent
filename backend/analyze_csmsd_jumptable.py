import sys
import struct
import bisect

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

TABLE_BASE = 0x000E20EC
TYPE_MIN = 0x19   # 25
TYPE_MAX = 0x19 + 0x29  # 25 + 41 = 66


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        ta = td = None
        syms = []
        for sec in elf.iter_sections():
            if sec.name == ".text":
                ta, td = sec.header.sh_addr, sec.data()
            if sec.header.sh_type == "SHT_SYMTAB":
                for sym in sec.iter_symbols():
                    if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
                        syms.append((sym["st_value"], sym.name))
        smap = dict(syms)
        starts = sorted(smap)

        def nearest(a):
            i = bisect.bisect_right(starts, a) - 1
            if i < 0:
                return "?"
            st = starts[i]
            return f"{smap[st]}+{a-st}" if a != st else smap[st]

        print("JUMP TABLE (EquipCtrlNet::OnMessage):")
        for idx in range(0, TYPE_MAX - TYPE_MIN + 1):
            va = TABLE_BASE + idx * 4
            off = va - ta
            word = struct.unpack_from("<I", td, off)[0]
            t = TYPE_MIN + idx
            print(f"  type {t:3d} (0x{t:02x}): -> 0x{word:08x}  {nearest(word)}")

    print("""
Known handler context (from call sites):
  subtype@0xC == 3 -> PING_SERVER_RMS (log only)
  subtype@0xC == 5 -> bl 0xcb104
  subtype@0xC == 1 -> ignore (no-op)
""")


if __name__ == "__main__":
    main()
