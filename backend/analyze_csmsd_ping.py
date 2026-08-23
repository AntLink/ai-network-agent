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
        for sec in elf.iter_sections():
            if sec.name == ".text":
                ta, td = sec.header.sh_addr, sec.data()
            if sec.name == ".rodata":
                ro_addr, ro_data = sec.header.sh_addr, sec.data()

        md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)

        def dump(start, end, title):
            print(f"\n{'='*78}\n{title} (0x{start:08x}-0x{end:08x})\n{'='*78}")
            code = td[start - ta: end - ta]
            regs = {}
            for ins in md.disasm(code, start):
                m, ops = ins.mnemonic, ins.op_str
                note = ""
                if m == "movw" and ", #" in ops:
                    d, s = ops.split(", #")
                    try:
                        regs[d] = int(s, 16) if s.startswith("0x") else int(s)
                    except ValueError:
                        pass
                elif m == "movt" and ", #" in ops:
                    d, s = ops.split(", #")
                    try:
                        hi = int(s, 16) if s.startswith("0x") else int(s)
                        lo = regs.get(d, 0) & 0xFFFF
                        va = (hi << 16) | lo
                        if ro_addr <= va < ro_addr + len(ro_data):
                            e = ro_data.find(b"\x00", va - ro_addr)
                            sv = ro_data[va - ro_addr:e].decode("ascii", "replace")
                            note = f'   ; str "{sv[:60]}"'
                            regs[d] = va
                    except ValueError:
                        pass
                print(f"  {ins.address:08x}: {m:8s} {ops}{note}")

        # PING area of EquipCtrlNet::OnMessage
        dump(0x000e25e0, 0x000e27b0, "OnMessage: post-dispatch / PING_SERVER_RMS region")

        # UpConvertMeasureCtrl entry: read hdr fields + initial switch
        dump(0x0011e0d4, 0x0011e240, "UpConvertMeasureCtrl entry")


if __name__ == "__main__":
    main()
