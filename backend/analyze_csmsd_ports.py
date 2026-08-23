import struct
import sys

from elftools.elf.elffile import ELFFile

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

PORTS = {
    3302: "0x0CE6",
    3303: "0x0CE7",
    3304: "0x0CE8",
    3305: "0x0CE9",
    3306: "0x0CEA",
    3307: "0x0CEB",
}


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)

        # ---- collect executable sections -----------------------------------
        sections = []
        for sec in elf.iter_sections():
            if sec.header.sh_type == "SHT_NOBITS":
                continue
            data = sec.data()
            sections.append((sec.name, sec.header.sh_addr, data))

        # ---- collect function symbols ---------------------------------------
        funcs = []
        for sec in elf.iter_sections():
            if sec.header.sh_type not in ("SHT_SYMTAB", "SHT_DYNSYM"):
                continue
            for sym in sec.iter_symbols():
                if sym["st_info"]["type"] == "STT_FUNC" and sym["st_value"]:
                    funcs.append((sym["st_value"], sym.name))
        funcs = sorted(set(funcs))

        import bisect
        starts = [a for a, _ in funcs]

        def enclosing(addr):
            i = bisect.bisect_right(starts, addr) - 1
            if i >= 0:
                return funcs[i][1]
            return "??"

        # ---- search for port words in each section ---------------------------
        print("=" * 78)
        print("  PORT CONSTANT REFERENCES (literal-pool words)")
        print("=" * 78)
        for port, hexs in sorted(PORTS.items()):
            pattern = struct.pack("<I", port)
            hits = []
            for name, addr, data in sections:
                if name not in (".text", ".rodata", ".data"):
                    continue
                idx = data.find(pattern)
                while idx != -1:
                    va = addr + idx
                    # filter obvious noise: value must be word-aligned-ish
                    hits.append((name, va))
                    idx = data.find(pattern, idx + 1)
            print(f"\n--- port {port} ({hexs}): {len(hits)} raw hits ---")
            shown = 0
            for name, va in hits:
                if name != ".text":
                    continue
                fn = enclosing(va)
                print(f"  {name} @ 0x{va:08x}  in <{fn}>")
                shown += 1
                if shown >= 40:
                    break


if __name__ == "__main__":
    main()
