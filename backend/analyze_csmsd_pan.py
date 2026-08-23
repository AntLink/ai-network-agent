import sys
import bisect

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN

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
        starts = sorted((v, n) for n, (v, s) in syms.items())
        start_addrs = [a for a, _ in starts]

        def nearest(a):
            i = bisect.bisect_right(start_addrs, a) - 1
            if i < 0:
                return "?"
            st, nm = starts[i]
            return nm if a == st else f"{nm}+0x{a-st:x}"

        def read_str(va):
            off = va - ro_addr
            if 0 <= off < len(ro_data):
                e = ro_data.find(b"\x00", off)
                return ro_data[off:e].decode("ascii", "replace")
            return None

        md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)

        for fname in ["_ZN13CEquipControl12OnStatusCtrlEPK13SEquipCtrlMsgP14CNetConnectionIvE",
                      "_ZN13CEquipControl13OnPanDispCtrlEPK13SEquipCtrlMsgP14CNetConnectionIvE"]:
            va, sz = syms[fname]
            addr = va & ~1
            code = td[addr - ta: addr - ta + sz * 4]
            ins_list = list(md.disasm(code, addr))
            print(f"\n{'='*78}\n{fname}\n@0x{va:08x} sz={sz} ({len(ins_list)} ins)\n{'='*78}")

            regs = {}
            for ins in ins_list:
                m, ops = ins.mnemonic, ins.op_str
                note = ""
                # track string loads into r1 (log fmt) via movw/movt pair
                if m in ("movw", "movt") and ", #" in ops:
                    d, s = ops.split(", #")
                    try:
                        val = int(s, 16) if s.startswith("0x") else int(s)
                        if m == "movt":
                            lo = regs.get(d, 0) & 0xFFFF
                            va2 = (val << 16) | lo
                            s2 = read_str(va2)
                            if s2 and len(s2) > 4:
                                note = f'   ; "{s2[:70]}"'
                            regs[d] = va2
                        else:
                            regs[d] = val
                    except ValueError:
                        pass
                elif m == "bl":
                    try:
                        tgt = int(ops.replace("#", ""), 16)
                        fn = nearest(tgt)
                        if not fn.startswith("_Z") or "Send" in fn or "send" in fn:
                            note = f"   ; -> {fn[:60]}"
                        else:
                            short = fn.split("(")[0].split("+")[0]
                            dem = short.split("9")[-1] if "9" in short else short
                            note = f"   ; -> {dem[-55:]}"
                    except ValueError:
                        pass
                elif m == "cmp" and "#" in ops:
                    try:
                        imm = int(ops.split("#")[1], 0)
                        if imm < 100:
                            note = f"   ; val={imm}"
                    except ValueError:
                        pass
                print(f"  {ins.address:08x}: {m:8s} {ops}{note}")


if __name__ == "__main__":
    main()
