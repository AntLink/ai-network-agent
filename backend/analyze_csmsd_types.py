import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN

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

    md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)

    # ---- 1) xrefs into Greeting(0x1236d8)/Pan(0x1236f0)/Measure(0x123720) ----
    va, sz = syms["_ZN11CMetricsNet9OnMessageEPKvj"]
    code = td[va - ta: va - ta + sz * 4]
    ins_all = list(md.disasm(code, va))
    print("XREFS into handler blocks:")
    targets = {"GREETING": 0x1236D8, "PAN": 0x1236F0, "MEASURE": 0x123720,
               "SUPERUSER": 0x1232A0, "STATUS": 0x123698}
    for label, t in targets.items():
        srcs = []
        for i, ins in enumerate(ins_all):
            if ins.mnemonic.startswith("b") and ins.op_str.replace("#", "") == hex(t)[2:] or \
               ins.op_str.endswith(hex(t)):
                srcs.append(ins.address)
        print(f"  {label} 0x{t:x}: {[hex(s) for s in srcs]}")

    def ctx(addr, back=10):
        i = next((k for k, x in enumerate(ins_all) if x.address == addr), None)
        if i is None:
            return
        print(f"  --- ctx before 0x{addr:08x}:")
        for x in ins_list[max(0, i - back):i + 1]:
            print(f"      {x.address:08x}: {x.mnemonic:8s} {x.op_str}")

    for label in ("GREETING", "PAN", "MEASURE"):
        t = targets[label]
        for s in [s for s in [ins.address for ins in ins_all]
                  if any(x.op_str.endswith(hex(t)) and x.address == s for x in ins_all)]:
            pass
    # simpler: context per found source
    for label, t in targets.items():
        srcs = [ins.address for ins in ins_all
                if ins.mnemonic[0] == "b" and ins.op_str.endswith(hex(t))]
        for s in srcs[:2]:
            print()
            ctx(s)

    # ---- 2) CMetricsNet::OnStatusCtrl full ------------------------------------
    va2, sz2 = syms["_ZN11CMetricsNet12OnStatusCtrlERK11SMetricsMsg"]
    print(f"\n{'='*78}\nCMetricsNet::OnStatusCtrl @0x{va2:08x} sz={sz2}\n{'='*78}")
    ins2 = list(md.disasm(td[va2 - ta: va2 - ta + sz2 * 4], va2))
    ro_addr = ro_data = None
    for sec in elf.iter_sections():
        if sec.name == ".rodata":
            ro_addr, ro_data = sec.header.sh_addr, sec.data()

    regs = {}
    for ins in ins2:
        m, ops = ins.mnemonic, ins.op_str
        note = ""
        if m in ("movw", "movt") and ", #" in ops:
            d, s = ops.split(", #")
            try:
                v = int(s, 16) if s.startswith("0x") else int(s)
                if m == "movw":
                    regs[d] = v
                else:
                    lo = regs.get(d, 0) & 0xFFFF
                    v2 = (v << 16) | lo
                    regs[d] = v2
                    off = v2 - ro_addr
                    if 0 <= off < len(ro_data):
                        e = ro_data.find(b"\x00", off)
                        s2 = ro_data[off:e].decode("ascii", "replace")
                        if len(s2) > 5:
                            note = f'   ; "{s2[:70]}"'
            except Exception:
                pass
        elif m == "cmp" and "#" in ops:
            try:
                h = ops.split("#")[1]
                imm = int(h, 16) if h.startswith("0x") else int(h)
                if imm < 100:
                    note = f"   ; val={imm}"
            except Exception:
                pass
        print(f"{ins.address:08x}: {m:8s} {ops}{note}")


if __name__ == "__main__":
    main()
