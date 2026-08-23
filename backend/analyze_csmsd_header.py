import sys
import struct

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

WANT_FUNCS = [
    "_ZN14CNetConnectionI13CEquipCtrlNetE4SendEPKvj",
    "_ZN13CEquipCtrlNet4SendEPKvj",
    "_ZN14CNetConnectionI13CEquipCtrlNetE9OnMessageEPKvj",
    "_ZN13CEquipCtrlNet9OnMessageEPKvj",
]


def find_syms(elf):
    out = {}
    for sec in elf.iter_sections():
        if sec.header.sh_type != "SHT_SYMTAB":
            continue
        for sym in sec.iter_symbols():
            nm = sym.name
            if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
                if ("CEquipCtrlNet" in nm and ("Send" in nm or "OnMessage" in nm or "OnConnect" in nm)) or nm in WANT_FUNCS:
                    out[nm] = (sym["st_value"], sym["st_size"])
    return out


def disasm(td, ta, va, size):
    addr = va & ~1
    mode = CS_MODE_THUMB if (va & 1) else CS_MODE_ARM
    code = td[addr - ta: addr - ta + max(size * 4, 64)]
    md = Cs(CS_ARCH_ARM, mode | CS_MODE_LITTLE_ENDIAN)
    lines = []
    for ins in md.disasm(code, addr):
        lines.append(f"    {ins.address:08x}: {ins.mnemonic:8s} {ins.op_str}")
        if len(lines) > 400:
            break
    return lines


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        ta = td = None
        for sec in elf.iter_sections():
            if sec.name == ".text":
                ta, td = sec.header.sh_addr, sec.data()

        syms = find_syms(elf)
        print("matched symbols:")
        for nm, (va, sz) in sorted(syms.items(), key=lambda kv: kv[1][0]):
            print(f"  0x{va:08x} sz={sz} {nm}")

        # disassemble the most interesting ones
        for pick in ["_ZN13CEquipCtrlNet4SendEPKvj", "_ZN13CEquipCtrlNet9OnMessageEPKvj"]:
            if pick in syms:
                va, sz = syms[pick]
                print(f"\n{'=' * 78}\nDISASM {pick} @0x{va:08x} sz={sz}\n{'=' * 78}")
                for ln in disasm(td, ta, va, sz):
                    print(ln)


if __name__ == "__main__":
    main()
