import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

SEND_ERROR = 0x000defec


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        ta = td = None
        syms = {}
        ro_addr = ro_data = None
        for sec in elf.iter_sections():
            if sec.name == ".text":
                ta, td = sec.header.sh_addr, sec.data()
            if sec.name == ".rodata":
                ro_addr, ro_data = sec.header.sh_addr, sec.data()
            if sec.header.sh_type == "SHT_SYMTAB":
                for sym in sec.iter_symbols():
                    if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
                        syms[sym.name] = (sym["st_value"], sym["st_size"])

        def read_str(va):
            off = va - ro_addr
            if 0 <= off < len(ro_data):
                e = ro_data.find(b"\x00", off)
                return ro_data[off:e].decode("ascii", "replace")
            return None

        name = "_ZN13CEquipCtrlNet9OnMessageEPKvj"
        va, sz = syms[name]
        addr = va & ~1
        code = td[addr - ta: addr - ta + sz * 4]
        md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
        ins_list = list(md.disasm(code, addr))

        print(f"OnMessage @0x{va:08x}, {len(ins_list)} instructions")

        # find all bl targets + preceding mov r2 imm
        calls = []
        for idx, ins in enumerate(ins_list):
            if ins.mnemonic == "bl":
                try:
                    tgt = int(ins.op_str.replace("#", ""), 16)
                except ValueError:
                    continue
                errcode = None
                for j in range(idx - 1, max(0, idx - 15), -1):
                    pj = ins_list[j]
                    if pj.mnemonic == "mov" and pj.op_str.startswith("r2, #"):
                        errcode = int(pj.op_str.split("#")[1], 0)
                        break
                    if pj.mnemonic == "bl":
                        break
                calls.append((ins.address, tgt, errcode))

        print("\nAll call sites (addr, target, r2-before):")
        for a, t, e in calls:
            note = ""
            if t == SEND_ERROR:
                note = f"  <<< SendError(err={e})"
            print(f"  0x{a:08x}: bl 0x{t:08x}{note}")

        # also print string refs (r1 = string before bl 0xffce8 which is printf-ish)
        print("\nString refs (log messages) in order:")
        regs = {}
        for ins in ins_list:
            m = ins.mnemonic
            ops = ins.op_str
            if m == "movw" and "r1," in ops:
                try:
                    val = int(ops.split("#")[1], 0)
                    regs["r1w"] = val
                except (ValueError, IndexError):
                    pass
            elif m == "movt" and "r1," in ops:
                try:
                    hi = int(ops.split("#")[1], 0)
                    lo = regs.get("r1w", 0) & 0xFFFF
                    va1 = (hi << 16) | lo
                    s = read_str(va1)
                    if s and len(s) > 3:
                        print(f"  0x{ins.address:08x}: {s[:110]}")
                except (ValueError, IndexError):
                    pass


if __name__ == "__main__":
    main()
