import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

FUNC_START = 0x000E1D18
FUNC_END = FUNC_START + 2964 * 2  # generous


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        ta = td = None
        ro_addr = ro_data = None
        for sec in elf.iter_sections():
            if sec.name == ".text":
                ta, td = sec.header.sh_addr, sec.data()
            if sec.name == ".rodata":
                ro_addr, ro_data = sec.header.sh_addr, sec.data()

        md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
        code = td[FUNC_START - ta: FUNC_END - ta]
        ins_list = list(md.disasm(code, FUNC_START))

        # build xref map: target -> [sources]
        xrefs = defaultdict(list)
        by_addr = {}
        for ins in ins_list:
            by_addr[ins.address] = ins
            if ins.mnemonic in ("b", "beq", "bne", "blt", "ble", "bgt", "bge", "bls", "bhs", "blo", "bhi", "beq"):
                op = ins.op_str.replace("#", "")
                try:
                    tgt = int(op, 16)
                    xrefs[tgt].append(ins.address)
                except ValueError:
                    pass

        # who jumps to the PING log block 0xe278c?
        print("XREFS -> 0xe278c (PING log):", [hex(x) for x in xrefs.get(0xE278C, [])])
        print("XREFS -> 0xe2770 (ping handler call):", [hex(x) for x in xrefs.get(0xE2770, [])])

        # dump context before each xref source
        def ctx(addr, back=14):
            i = next((k for k, ins in enumerate(ins_list) if ins.address == addr), None)
            if i is None:
                return
            print(f"\n--- context before 0x{addr:08x} ---")
            for ins in ins_list[max(0, i - back):i + 1]:
                regs = ""
                print(f"  {ins.address:08x}: {ins.mnemonic:8s} {ins.op_str}")

        for src in xrefs.get(0xE278C, []):
            ctx(src)
        for src in xrefs.get(0xE2770, []):
            ctx(src)


if __name__ == "__main__":
    main()
