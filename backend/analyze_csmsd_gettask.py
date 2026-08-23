import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        ta = td = None
        syms = {}
        for sec in elf.iter_sections():
            if sec.name == ".text":
                ta, td = sec.header.sh_addr, sec.data()
            if sec.header.sh_type == "SHT_SYMTAB":
                for sym in sec.iter_symbols():
                    if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
                        syms[sym.name] = (sym["st_value"], sym["st_size"])

        for name in ["_ZN10CHwControl7GetTaskEP14CNetConnectionIvEN7SSmsMsg8EMsgTypeERSt10shared_ptrI5CTaskE"]:
            va, sz = syms[name]
            addr = va & ~1
            code = td[addr - ta: addr - ta + sz * 4]
            md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
            ins_list = list(md.disasm(code, addr))
            print(f"{name} @0x{va:08x} sz={sz} ({len(ins_list)} ins)")
            print("=" * 78)
            for ins in ins_list:
                line = f"  {ins.address:08x}: {ins.mnemonic:8s} {ins.op_str}"
                # annotate ldrh comparisons with u16 immediates
                if ins.mnemonic == "cmp" and "#" in ins.op_str:
                    try:
                        imm = int(ins.op_str.split("#")[1], 0)
                        if 20 <= imm <= 300:
                            line += f"   ; <<< msgType {imm}"
                    except ValueError:
                        pass
                if ins.mnemonic == "sub" and "#0x" in ins.op_str:
                    try:
                        imm = int(ins.op_str.split("#")[1], 16)
                        if 20 <= imm <= 300:
                            line += f"   ; <<< msgType base {imm}"
                    except ValueError:
                        pass
                print(line)


if __name__ == "__main__":
    main()
