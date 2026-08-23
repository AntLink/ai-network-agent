import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

PICKS = [
    ("_ZN13CEquipCtrlNet9SendErrorERKN7SSmsMsg4SHdrEm", 0),
    ("_ZN13CEquipCtrlNet9OnMessageEPKvj", 160),  # first N instructions only
    ("_ZN13CEquipCtrlNet9OnConnectEv", 0),
]


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        ta = td = None
        for sec in elf.iter_sections():
            if sec.name == ".text":
                ta, td = sec.header.sh_addr, sec.data()
            if sec.header.sh_type == "SHT_SYMTAB":
                syms = {}
                for sym in sec.iter_symbols():
                    if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
                        syms[sym.name] = (sym["st_value"], sym["st_size"])

        for name, maxins in PICKS:
            if name not in syms:
                print(f"!! {name} not found")
                continue
            va, sz = syms[name]
            addr = va & ~1
            mode = CS_MODE_THUMB if (va & 1) else CS_MODE_ARM
            code = td[addr - ta: addr - ta + sz * 4 + 32]
            md = Cs(CS_ARCH_ARM, mode | CS_MODE_LITTLE_ENDIAN)
            print(f"\n{'=' * 78}\n{name} @0x{va:08x} sz={sz}\n{'=' * 78}")
            n = 0
            for ins in md.disasm(code, addr):
                print(f"    {ins.address:08x}: {ins.mnemonic:8s} {ins.op_str}")
                n += 1
                if maxins and n >= maxins:
                    break


if __name__ == "__main__":
    main()
