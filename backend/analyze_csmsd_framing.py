import sys
import bisect

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

WANT = ["HeaderSize", "BodySize", "Delimiter"]


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)

        # text section
        text = None
        for sec in elf.iter_sections():
            if sec.name == ".text":
                text = (sec.header.sh_addr, sec.data())
        ta, td = text

        syms = []
        for sec in elf.iter_sections():
            if sec.header.sh_type != "SHT_SYMTAB":
                continue
            for sym in sec.iter_symbols():
                if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
                    syms.append((sym["st_value"], sym.name, sym["st_size"]))
        syms = sorted(set(syms))

        targets = [(va, name, size) for va, name, size in syms
                   if any(w in name for w in WANT) and size <= 64]
        print(f"{len(targets)} small framing functions found\n")

        for va, name, size in sorted(targets):
            addr = va & ~1  # thumb bit
            mode = CS_MODE_THUMB if (va & 1) else CS_MODE_ARM
            code = td[addr - ta: addr - ta + max(size, 4) * 2]
            md = Cs(CS_ARCH_ARM, mode | CS_MODE_LITTLE_ENDIAN)
            print(f"--- 0x{va:08x} sz={size} {'THUMB' if (va & 1) else 'ARM'} {name}")
            try:
                for ins in md.disasm(code, addr):
                    print(f"    {ins.address:08x}: {ins.mnemonic:8s} {ins.op_str}")
                    if ins.mnemonic in ("bx", "pop") and "lr" in ins.op_str or ins.mnemonic == "bx":
                        break
            except Exception as e:
                print(f"    <disasm error: {e}>")
            print()


if __name__ == "__main__":
    main()
