import sys

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

import bisect
starts = sorted((v, n) for n, (v, s) in syms.items())
sad = [a for a, _ in starts]


def nearest(a):
    i = max(bisect.bisect_right(sad, a) - 1, 0)
    st, nm = starts[i]
    return nm if st == a else f"{nm}+0x{a-st:x}"


def read_str(v):
    off = v - ro_addr
    if 0 <= off < len(ro_data):
        e = ro_data.find(b"\x00", off)
        return ro_data[off:e].decode("ascii", "replace")
    return None


md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)

# LINEAR ascending dump of the gate region in CMetricsNet::OnMessage
START = 0x123138
END = 0x123280
code = td[START - ta: END - ta]
ins_list = sorted(md.disasm(code, START), key=lambda i: i.address)

print("LINEAR DUMP CMetricsNet::OnMessage gate region 0x123138-0x123280")
print("(r5 = request SMetricsMsg*, r4 = CMetricsNet* this)")
print("=" * 78)
regs = {}
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
                s2 = read_str(v2)
                if s2 and len(s2) > 4:
                    note = f'   ; "{s2[:60]}"'
        except ValueError:
            pass
    elif m == "bl":
        try:
            t = int(ops.replace("#", ""), 16)
            note = f"   ; -> {nearest(t)[-58:]}"
        except ValueError:
            pass
    print(f"{ins.address:08x}: {m:8s} {ops}{note}")
