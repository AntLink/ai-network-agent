import sys
import struct
import bisect

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        ta = td = None
        ro_addr = ro_data = None
        syms = {}
        for sec in elf.iter_sections():
            if sec.name == ".text":
                ta, td = sec.header.sh_addr, sec.data()
            if sec.name == ".rodata":
                ro_addr, ro_data = sec.header.sh_addr, sec.data()
            if sec.header.sh_type == "SHT_SYMTAB":
                for sym in sec.iter_symbols():
                    if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
                        syms[sym.name] = (sym["st_value"], sym["st_size"])

        def read_str(va, maxlen=80):
            off = va - ro_addr
            if 0 <= off < len(ro_data):
                e = ro_data.find(b"\x00", off)
                return ro_data[off:e].decode("ascii", "replace")[:maxlen]
            return None

        name = "_GLOBAL__sub_I__ZN13CEquipCtrlNet12m_versionMapE"
        va, sz = syms[name]
        addr = va & ~1
        code = td[addr - ta: addr - ta + sz * 4]
        md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
        ins_list = list(md.disasm(code, addr))

        print(f"{name} @0x{va:08x} sz={sz}, {len(ins_list)} instructions")

        # Track register values for mov/movt/ldr(literal) to spot map keys/values
        regs = {}
        inserts = []
        strrefs = []
        for idx, ins in enumerate(ins_list):
            m, ops = ins.mnemonic, ins.op_str
            if m == "mov" and "," in ops:
                d, s = [x.strip() for x in ops.split(",")]
                if s.startswith("#"):
                    try:
                        regs[d] = int(s[1:], 0)
                    except ValueError:
                        pass
            elif m == "movt" and "," in ops:
                d, s = [x.strip() for x in ops.split(",")]
                if s.startswith("#"):
                    try:
                        hi = int(s[1:], 0)
                        lo = regs.get(d, 0) & 0xFFFF
                        regs[d] = (hi << 16) | lo
                    except ValueError:
                        pass
            elif m == "movw" and "," in ops:
                d, s = [x.strip() for x in ops.split(",")]
                if s.startswith("#"):
                    try:
                        regs[d] = int(s[1:], 0)
                    except ValueError:
                        pass
            elif m == "ldr" and "=" in ops:
                # literal pseudo-op: ldr rX, =value or =label
                d, s = [x.strip() for x in ops.split("=", 1)]
                d = d.strip()
                s = s.strip()
                if s.startswith(("0x",)) and s[1:].isdigit() is False:
                    pass
                try:
                    if s.startswith("0x"):
                        regs[d] = int(s, 16)
                    elif s.isdigit():
                        regs[d] = int(s)
                    else:
                        # label -> resolve via literal pool at end of function
                        pass
                except Exception:
                    pass
            elif m == "bl":
                strv = regs.get("r1")
                if strv and ro_addr <= strv < ro_addr + len(ro_data):
                    s = read_str(strv)
                    if s:
                        strrefs.append((ins.address, s))

        print("\nSTRING REFS in init function:")
        for a, s in strrefs[:40]:
            print(f"  0x{a:08x}: {s}")

        # Also dump raw instruction stream around store-pair patterns (map inserts)
        print("\nFULL DISASM (first 500):")
        for ins in ins_list[:500]:
            note = ""
            v = regs.get("r1") if ins.mnemonic.startswith("ldr") else None
            print(f"  {ins.address:08x}: {ins.mnemonic:8s} {ins.op_str}")


if __name__ == "__main__":
    main()
