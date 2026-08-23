import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"


def die_name(die):
    attr = die.attributes.get("DW_AT_name")
    return attr.value.decode() if attr else None


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        dw = elf.get_dwarf_info()
        for cu in dw.iter_CUs():
            top = cu.get_top_DIE()
            n = die_name(top) or "?"
            at = cu._abbrev_table
            cnt = Counter(a.decl["tag"] for a in at._abbrev_map.values())
            has_enum = "DW_TAG_enumeration_type" in cnt
            has_struct = any("class_type" in t or "structure_type" in t for t in cnt)
            if has_enum or has_struct:
                short = n.split("/")[-1].split("\\")[-1]
                print(f"{short:<28} v{cu.header.version} enum={cnt.get('DW_TAG_enumeration_type', 0):<4} "
                      f"struct={cnt.get('DW_TAG_structure_type', 0)} class={cnt.get('DW_TAG_class_type', 0)}"
                      f" total_tags={len(cnt)}")


if __name__ == "__main__":
    main()
