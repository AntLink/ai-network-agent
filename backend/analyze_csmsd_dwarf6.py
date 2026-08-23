import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile
from elftools.dwarf.enums import ENUM_DW_TAG

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        dw = elf.get_dwarf_info()
        for cu in dw.iter_CUs():
            top = cu.get_top_DIE()
            n = top.attributes.get("DW_AT_name")
            if not n or b"EquipCtrlNet" not in n.value:
                continue

            ab_sec = elf.get_section_by_name(".debug_abbrev")
            data = ab_sec.data()
            ao = cu._abbrev_offset
            pos = ao
            codes = {}
            while pos < len(data):
                code = 0
                shift = 0
                while True:
                    b = data[pos]
                    pos += 1
                    code |= (b & 0x7F) << shift
                    shift += 7
                    if not (b & 0x80):
                        break
                if code == 0:
                    break
                tag = 0
                shift = 0
                while True:
                    b = data[pos]
                    pos += 1
                    tag |= (b & 0x7F) << shift
                    shift += 7
                    if not (b & 0x80):
                        break
                has_children = data[pos]
                pos += 1
                while True:
                    aname = data[pos]
                    aform = data[pos + 1]
                    pos += 2
                    if aname == 0 and aform == 0:
                        break
                codes[code] = tag

            from collections import Counter
            cnt = Counter(codes.values())
            print("tag values used by this CU's abbrevs:")
            unknown_tags = []
            for tv, c in sorted(cnt.items()):
                try:
                    name = ENUM_DW_TAG[tv]
                except Exception:
                    name = f"UNKNOWN(0x{tv:04x})"
                    unknown_tags.append(tv)
                print(f"  tag {tv:>6} x{c:<4} {name}")
            print(f"\nunknown tags: {unknown_tags}")
            break


if __name__ == "__main__":
    main()
