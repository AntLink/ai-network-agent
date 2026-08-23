import sys
import bisect
import pickle

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"
ADDRS = [0x11E5E4, 0x11E634, 0x11E654, 0x11E67C, 0x120440, 0x120448]


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
                        syms.append((sym["st_value"], sym.name, sym["st_size"]))
        syms.sort()
        starts = [s[0] for s in syms]

        def enclosing(a):
            i = bisect.bisect_right(starts, a) - 1
            return syms[i] if i >= 0 else (0, "?", 0)

        for a in ADDRS:
            va, name, size = enclosing(a)
            print(f"\naddr 0x{a:08x} -> {name} @0x{va:08x} sz={size}")

        # disassemble windows around each unique function hit
        seen_funcs = set()
        md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
        for a in ADDRS:
            va, name, size = enclosing(a)
            if name in seen_funcs:
                continue
            seen_funcs.add(name)
            start = max(va & ~1, a - 0x60)
            code = td[start - ta: min(va + size * 4 if size else a + 0x100, a + 0xC0) - ta]
            print(f"\n{'='*78}\nWINDOW around 0x{a:08x} in {name}\n{'='*78}")
            for ins in md.disasm(code, start):
                mark = "   <<<< LINE2673" if ins.address == a else ""
                print(f"  {ins.address:08x}: {ins.mnemonic:8s} {ins.op_str}{mark}")


if __name__ == "__main__":
    main()
