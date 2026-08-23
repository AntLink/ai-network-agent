import sys
import collections

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
            cu_name = die_name(top) or ""
            if "EquipCtrlNet" not in cu_name:
                continue
            print(f"CU: {cu_name} version={cu.header.version}")
            dies = list(cu.iter_DIEs())
            print(f"total DIEs: {len(dies)}")
            tags = collections.Counter(d.tag for d in dies)
            for t, c in tags.most_common():
                print(f"  {t}: {c}")

            # named enums anywhere?
            enums = [d for d in dies if d.tag == "DW_TAG_enumeration_type"]
            print(f"\nenumeration_type DIEs: {len(enums)}")
            for d in enums[:10]:
                n = die_name(d)
                kids = list(d.iter_children())
                print(f"  name={n} children={len(kids)} has_size={'DW_AT_byte_size' in d.attributes}")

            # typedefs containing 'Msg'
            print("\ntypedefs with Msg/Err in name:")
            for d in dies:
                if d.tag == "DW_TAG_typedef":
                    n = die_name(d) or ""
                    if "Msg" in n or "Err" in n or "Hdr" in n:
                        t = d.attributes.get("DW_AT_type")
                        ref = t.value if t else None
                        tgt = None
                        if ref is not None:
                            td_die = next((x for x in dies if x.offset == ref), None)
                            tgt = (td_die.tag if td_die else "?", die_name(td_die) if td_die else "?")
                        print(f"  {n} -> {tgt}")
            break


if __name__ == "__main__":
    main()
