import sys
import bisect

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

f = open(ELF_PATH, "rb")
elf = ELFFile(f)
ta = td = ro_addr = ro_data = None
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

md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
starts = sorted((v, n) for n, (v, s) in syms.items())
sad = [a for a, _ in starts]


def nearest(a):
    i = max(bisect.bisect_right(sad, a) - 1, 0)
    st, nm = starts[i]
    return nm if st == a else f"{nm}+0x{a-st:x}"


def dump_fn(name, max_ins=None):
    va, sz = syms[name]
    ins_list = list(md.disasm(td[va - ta: va - ta + sz * 4], va))
    print(f"\n{'='*78}\n{name}\n@0x{va:08x} sz={sz} ({len(ins_list)} ins)\n{'='*78}")
    regs = {}
    n = 0
    for ins in ins_list:
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
                        if len(s2) > 4:
                            note = f'   ; "{s2[:80]}"'
            except Exception:
                pass
        elif m == "bl":
            note = f"   ; -> {nearest(int(ops.replace('#',''),16))[-58:]}"
        elif m == "cmp" and "#" in ops:
            try:
                h = ops.split("#")[1]
                imm = int(h, 16) if h.startswith("0x") else int(h)
                if imm < 200:
                    note = f"   ; val={imm}"
            except Exception:
                pass
        print(f"{ins.address:08x}: {m:8s} {ops}{note}")
        n += 1
        if max_ins and n >= max_ins:
            break


dump_fn("_ZN8CMetrics24OnMeasurementGreetingReqERK11SMetricsMsgP11CMetricsNet")
