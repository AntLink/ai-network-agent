import sys
import struct
import bisect

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)

        # ---- 1) symbols mentioning enums / errors under SSmsMsg --------------
        print("=" * 78)
        print("  SYMBOLS: SSmsMsg / EMsg / EErr enums")
        print("=" * 78)
        for sec in elf.iter_sections():
            if sec.header.sh_type != "SHT_SYMTAB":
                continue
            for sym in sec.iter_symbols():
                n = sym.name
                if ("SSmsMsg" in n and ("E" == n.split("SSmsMsg")[-1][:1] or "Err" in n or "EMsg" in n)) \
                        or ("EEquipCtrl" in n) or ("EDfCtrl" in n):
                    print(f"  {sym['st_value']:08x} sz={sym['st_size']} {n}")

        # ---- 2) rodata strings: error-ish text -------------------------------
        print("\n" + "=" * 78)
        print("  RODATA: error/message-type related strings")
        print("=" * 78)
        keys = [b"Unsupported", b"unsupported", b"Invalid msg", b"invalid msg",
                b"Unknown msg", b"unknown msg", b"MsgType", b"msgType",
                b"NotSupported", b"WrongState", b"Busy", b"EBusy"]
        for sec in elf.iter_sections():
            if sec.name != ".rodata":
                continue
            data = sec.data()
            base = sec.header.sh_addr
            for k in keys:
                i = data.find(k)
                seen = set()
                while i != -1 and len(seen) < 8:
                    s = data.rfind(b"\x00", max(0, i - 120), i)
                    e = data.find(b"\x00", i)
                    full = data[s + 1:e].decode("ascii", "replace")
                    if len(full) < 150 and full not in seen:
                        seen.add(full)
                        print(f"  @0x{base+s:08x}: {full}")
                    i = data.find(k, i + 1)

        # ---- 3) full OnMessage: find where 3/5/6 passed to SendError ---------
        print("\n" + "=" * 78)
        print("  ONMESSAGE: SendError call sites")
        print("=" * 78)
        ta = td = None
        syms = {}
        for sec in elf.iter_sections():
            if sec.name == ".text":
                ta, td = sec.header.sh_addr, sec.data()
            if sec.header.sh_type == "SHT_SYMTAB":
                for sym in sec.iter_symbols():
                    if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
                        syms[sym.name] = (sym["st_value"], sym["st_size"])

        name = "_ZN13CEquipCtrlNet9OnMessageEPKvj"
        va, sz = syms[name]
        addr = va & ~1
        code = td[addr - ta: addr - ta + sz * 4]
        md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
        ins_list = list(md.disasm(code, addr))
        for idx, ins in enumerate(ins_list):
            if ins.mnemonic == "bl" and "#0xdefec" in ins.op_str.lower().replace("0x", "#0x"):
                pass
            # find bl to SendError (0xdefec) and mov r2,#N shortly before
            if ins.mnemonic == "bl" and ins.op_str.endswith("#0xdefec"):
                # look back up to 12 instructions for mov r2,#imm
                ctx = []
                for j in range(max(0, idx - 12), idx):
                    ctx.append(f"{ins_list[j].mnemonic} {ins_list[j].op_str}")
                print(f"  CALL @0x{ins.address:08x}:")
                for c in ctx:
                    print(f"      {c}")
                print()


if __name__ == "__main__":
    main()
