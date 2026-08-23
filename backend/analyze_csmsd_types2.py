import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

f = open(ELF_PATH, "rb")
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

va, sz = syms["_ZN11CMetricsNet9OnMessageEPKvj"]
md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
ins_all = list(md.disasm(td[va - ta: va - ta + sz * 4], va))
by_addr = {i.address: i for i in ins_all}

HANDLER_BL = {
    0x123628: "OnDemodCtrl",
    0x123648: "OnSystemStateCtrl",
    0x123660: "OnOccupancyCtrl",
    0x123678: "OnPriorityCtrl",
    0x123690: "OnAntCtrl",
    0x12369C: "Net::OnStatusCtrl",
    0x1236B4: "OnAvdCtrl",
    0x1236CC: "OnOccupancyDfCtrl",
    0x1236E4: "** OnMeasurementGreetingReq **",
    0x1236FC: "** OnMeasurementPanReq **",
    0x123714: "OnBistCtrl",
    0x12372C: "** OnMeasureCtrl **",
    0x110088 - 0 + 0x1232B4: "OnSuperUserCtrl",  # bl at 0x1232b4
}

# find all branch sources per target
branches = {}
for ins in ins_all:
    if ins.mnemonic.startswith("b") and ins.mnemonic != "bl" and "#" in ins.op_str:
        try:
            t = int(ins.op_str.replace("#", ""), 16)
            branches.setdefault(t, []).append(ins.address)
        except ValueError:
            pass

# for each handler bl, walk backwards to find nearest preceding branch-target (block entry)
all_tgts = sorted(branches.keys())
import bisect
print("BLOCK ENTRIES -> HANDLER:")
for bl, name in sorted(HANDLER_BL.items()):
    i = bisect.bisect_left(all_tgts, bl) - 1
    # search up to 40 bytes back
    entry = None
    for j in range(i, -1, -1):
        if bl - all_tgts[j] < 48:
            entry = all_tgts[j]
        else:
            break
    srcs = branches.get(entry, []) if entry else []
    print(f"\n{name:<34} bl@0x{bl:x}  block=0x{entry:x} if any")
    for s in srcs[:4]:
        k = next(idx for idx, x in enumerate(ins_all) if x.address == s)
        print(f"   branch from 0x{s:08x}, context:")
        for x in ins_all[max(0, k - 8):k + 1]:
            print(f"      {x.address:08x}: {x.mnemonic:7s} {x.op_str}")
