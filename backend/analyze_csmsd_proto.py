import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

PATTERNS = [
    "EquipCtrl", "DfCtrl", "VCPCtrl", "RdsNet", "ScpiNet",
    "SmsMsg", "SmsHeader", "MsgHeader", "MessageHeader",
    "NetServer", "NetConnection", "Listen", "AcceptLoop",
    "8CServer", "6Server",
]


def demangle_simple(name):
    return name


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)

        funcs, objs = [], []
        for sec in elf.iter_sections():
            if sec.header.sh_type != "SHT_SYMTAB":
                continue
            for sym in sec.iter_symbols():
                t = sym["st_info"]["type"]
                if t == "STT_FUNC" and sym["st_value"]:
                    funcs.append((sym["st_value"], sym.name, sym["st_size"]))
                elif t == "STT_OBJECT" and sym["st_value"]:
                    objs.append((sym["st_value"], sym.name, sym["st_size"]))

        print(f"total func syms: {len(funcs)}, object syms: {len(objs)}")

        def dump(title, items, pats, limit=60):
            print("\n" + "=" * 78)
            print(f"  {title}")
            print("=" * 78)
            seen = set()
            count = 0
            for va, name, size in sorted(items):
                for p in pats:
                    if p in name:
                        key = name
                        if key in seen:
                            continue
                        seen.add(key)
                        print(f"  0x{va:08x} sz={size:<6} {name}")
                        count += 1
                        break
                if count >= limit:
                    break

        dump("NETWORK SERVER FUNCTIONS", funcs,
             ["EquipCtrlNet", "DfCtrlNet", "VCPCtrlNet", "RdsNet", "ScpiNet",
              "StartServer", "CreateServer", "ListenThread", "AcceptThread"])

        dump("MESSAGE / FRAMING FUNCTIONS", funcs,
             ["SmsMsg", "MsgHdr", "MsgHeader", "PackMsg", "UnpackMsg",
              "Serialize", "Deserialize", "Encode", "Decode"], limit=40)

        # class vtable/typeinfo names for protocol classes
        print("\n" + "=" * 78)
        print("  TYPEINFO / CLASS NAMES (protocol related)")
        print("=" * 78)
        with open(ELF_PATH, "rb") as g:
            pass
        names = set()
        for va, name, size in funcs:
            pass
        # typeinfo names live in rodata; scan symbol table for OBJECT "_ZTS"
        for va, name, size in sorted(objs):
            if "_ZTS" in name:
                import re
                m = re.match(r"_ZTS(\d+)", name[4:] if name.startswith("_ZTS") else name)
        # simpler: read .rodata strings that look like class names of interest
        for sec in elf.iter_sections():
            if sec.name != ".rodata":
                continue
            data = sec.data()
            base = sec.header.sh_addr
            idx = 0
            keys = ["EquipCtrlNet", "DfCtrlNet", "VCPCtrlNet", "RdsNet", "ScpiNet",
                    "CAudio", "CRDSProcessor", "CProcesorNode", "ProcessorNode"]
            found = {}
            for k in keys:
                b = k.encode()
                i = data.find(b)
                while i != -1:
                    # extract full NUL-terminated around
                    s = i
                    while s > 0 and data[s - 1] not in (0,) and chr(data[s - 1]).isalnum() or (s > 0 and data[s - 1] in (ord('_'),)):
                        s -= 1
                        if i - s > 60:
                            break
                    e = data.find(b"\x00", i)
                    full = data[s:e].decode("ascii", "replace")
                    if len(full) < 80:
                        found.setdefault(k, set()).add(full)
                    i = data.find(b, i + 1)
            for k, vs in found.items():
                print(f"\n[{k}]")
                for v in sorted(vs)[:15]:
                    print(f"   {v}")


if __name__ == "__main__":
    main()
