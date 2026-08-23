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

va, sz = syms["_ZN11CMetricsNet9OnMessageEPKvj"]
md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
ins_list = list(md.disasm(td[va - ta: va - ta + sz * 4], va))
starts = sorted((v, n) for n, (v, s) in syms.items())
sad = [a for a, _ in starts]
regs = {}
out = []
for ins in ins_list:
    m, ops = ins.mnemonic, ins.op_str
    note = ""
    if m == "cmp" and "#" in ops:
        try:
            h = ops.split("#")[1]
            imm = int(h, 16) if h.startswith("0x") else int(h)
            if imm < 300:
                note = f"   ; val={imm}"
        except Exception:
            pass
    elif m == "bl":
        try:
            t = int(ops.replace("#", ""), 16)
            i = max(bisect.bisect_right(sad, t) - 1, 0)
            stv, snm = starts[i]
            nm = snm if stv == t else f"{snm}+0x{t-stv:x}"
            note = "   ; " + nm[-65:]
        except Exception:
            pass
    elif m in ("movw", "movt") and ", #" in ops:
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
                    if len(s2) > 6:
                        note = f'   ; "{s2[:75]}"'
        except Exception:
            pass
    out.append(f"{ins.address:08x}: {m:8s} {ops}{note}")

open("analyze_csmsd_metrics_full.txt", "w", encoding="utf-8").write("\n".join(out))
print(f"wrote {len(out)} lines")
