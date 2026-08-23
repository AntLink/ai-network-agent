import sys
import struct
import bisect

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

HANDLERS = [
    ("type 25", 0x000CCFC4),
    ("type 26", 0x000D3288),
    ("type 27 MEASURE_CTRL", 0x000CABD8),
    ("type 28", 0x000D1A98),
    ("type 29", 0x000CF2A4),
    ("type 30", 0x000D44B8),
    ("type 31", 0x000CC8C0),
    ("type 33", 0x000D4F40),
    ("type 34", 0x000CFE00),
    ("type 50", 0x000D2A14),
    ("type 60 subtype5", 0x000CB104),
]


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        syms = []
        for sec in elf.iter_sections():
            if sec.header.sh_type == "SHT_SYMTAB":
                for sym in sec.iter_symbols():
                    if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
                        syms.append((sym["st_value"], sym.name))
        starts = sorted(s for s, _ in syms)

        def enclosing(a):
            i = bisect.bisect_right(starts, a) - 1
            if i < 0:
                return "?"
            st = starts[i]
            name = dict(syms)[st]
            suffix = f"+0x{a-st:x}" if a != st else ""
            return f"{name}{suffix}"

        print("HANDLER SYMBOLS:")
        for label, addr in HANDLERS:
            print(f"  {label:<22} bl 0x{addr:08x} -> {enclosing(addr)}")


if __name__ == "__main__":
    main()
