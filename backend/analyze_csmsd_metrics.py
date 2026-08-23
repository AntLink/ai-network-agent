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

        # all CMetricsNet methods
        print("CMetricsNet methods:")
        for n, (va, sz) in sorted(syms.items(), key=lambda kv: kv[1][0]):
            if n.startswith("_ZN11CMetricsNet") and ("OnMessage" in n or "OnConnect" in n or "Startup" in n or "SetupServer" in n):
                print(f"  0x{va:08x} sz={sz:<6} {n}")

        name = "_ZN11CMetricsNet9OnMessageEPKvj"
        if name not in syms:
            # search variants
            for n in syms:
                if "CMetricsNet" in n and "OnMessage" in n:
                    name = n
                    break
        va, sz = syms[name]
        addr = va & ~1
        code = td[addr - ta: addr - ta + sz * 4]
        md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
        ins_list = list(md.disasm(code, addr))
        print(f"\n{name}\n@0x{va:08x} sz={sz} ({len(ins_list)} instructions)\n")

        regs = {}

        def read_str(v):
            off = v - ro_addr
            if 0 <= off < len(ro_data):
                e = ro_data.find(b"\x00", off)
                return ro_data[off:e].decode("ascii", "replace")
            return None

        # find jump table: ldrls pc, [pc, rx, lsl #2]
        jt_va = None
        jt_min = jt_max = None
        for i, ins in enumerate(ins_list):
            if ins.mnemonic == "ldrls" and "pc," in ins.op_str and "lsl #2" in ins.op_str:
                print(f">>> JUMP TABLE at 0x{ins.address:08x}: {ins.mnemonic} {ins.op_str}")
                # preceding sub/cmp give bounds
                for j in range(i - 1, max(0, i - 6), -1):
                    pj = ins_list[j]
                    if pj.mnemonic == "sub" and ", #" in pj.op_str:
                        try:
                            jt_min = int(pj.op_str.split("#")[1], 16)
                            print(f"    bound sub: {pj.op_str} (min type={jt_min})")
                        except ValueError:
                            pass
                    if pj.mnemonic == "cmp" and ", #" in pj.op_str:
                        try:
                            jt_max = int(pj.op_str.split("#")[1], 16)
                            print(f"    bound cmp: {pj.op_str} (range size={jt_max})")
                        except ValueError:
                            pass
                jt_va = ins.address + 8
                break

        if jt_va and jt_min is not None and jt_max is not None:
            starts = sorted((v, n) for n, (v, s) in syms.items())
            sad = [a for a, _ in starts]
            print("\nJUMP TABLE ENTRIES:")
            for idx in range(0, jt_max + 1):
                wva = jt_va + idx * 4
                word = int.from_bytes(td[wva - ta:wva - ta + 4], "little")
                t = jt_min + idx
                fi = max(bisect.bisect_right(sad, word) - 1, 0)
                stv, snm = starts[fi]
                nm = snm if word == stv else f"{snm}+0x{word-stv:x}"
                short = nm
                if "_Z" in short:
                    # crude demangle: extract handler hint
                    for k in ("On", ):
                        pass
                print(f"  type {t:3d}: -> 0x{word:08x}  {short[:75]}")

        # string refs in function
        print("\nSTRING REFS:")
        for ins in ins_list:
            m, ops = ins.mnemonic, ins.op_str
            if m in ("movw", "movt") and ", #" in ops:
                d, s = ops.split(", #")
                try:
                    val = int(s, 16) if s.startswith("0x") else int(s)
                    if m == "movw":
                        regs[d] = val
                    else:
                        lo = regs.get(d, 0) & 0xFFFF
                        va2 = (val << 16) | lo
                        s2 = read_str(va2)
                        if s2 and len(s2) > 6:
                            print(f"  0x{ins.address:08x}: \"{s2[:90]}\"")
                        regs[d] = va2
                except ValueError:
                    pass


if __name__ == "__main__":
    import bisect
    main()
