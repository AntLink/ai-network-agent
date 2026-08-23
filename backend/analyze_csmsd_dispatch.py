import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        ta = td = None
        ro_addr = ro_data = None
        syms = []
        for sec in elf.iter_sections():
            if sec.name == ".text":
                ta, td = sec.header.sh_addr, sec.data()
            if sec.name == ".rodata":
                ro_addr, ro_data = sec.header.sh_addr, sec.data()
            if sec.header.sh_type == "SHT_SYMTAB":
                for sym in sec.iter_symbols():
                    if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
                        syms.append((sym["st_value"], sym.name))
        smap = dict(syms)

        md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
        code = td[0xE2028 - ta: 0xE2260 - ta]
        regs = {}
        print("DISPATCH HUB 0xe2028-0xe2260:")
        for ins in md.disasm(code, 0xE2028):
            m, ops = ins.mnemonic, ins.op_str
            note = ""
            if m == "bl":
                try:
                    tgt = int(ops.replace("#", ""), 16)
                    fn = smap.get(tgt)
                    if fn:
                        note = f"   ; -> {fn[:70]}"
                except ValueError:
                    pass
            print(f"  {ins.address:08x}: {m:8s} {ops}{note}")


if __name__ == "__main__":
    main()
