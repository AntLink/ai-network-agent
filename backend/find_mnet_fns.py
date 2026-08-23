import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

f = open(ELF_PATH, "rb")
elf = ELFFile(f)
for sec in elf.iter_sections():
    if sec.header.sh_type != "SHT_SYMTAB":
        continue
    for sym in sec.iter_symbols():
        n = sym.name
        if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
            if "CMetricsNet" in n and any(k in n for k in ("Callback", "Startup", "SetupServer", "OpenSocket", "SendError", "Send")):
                print(f"0x{sym['st_value']:08x} sz={sym['st_size']:<6} {n}")
