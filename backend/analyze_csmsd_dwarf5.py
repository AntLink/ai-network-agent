import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"


def main():
    import elftools
    print("pyelftools version:", getattr(elftools, "__version__", "?"))

    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        dw = elf.get_dwarf_info()
        for cu in dw.iter_CUs():
            top = cu.get_top_DIE()
            from elftools.dwarf.die import DIE
            n = top.attributes.get("DW_AT_name")
            if not n or b"EquipCtrlNet" not in n.value:
                continue

            # abbrev tables
            print("\nabbrev table codes:")
            ab = cu.structs.abbrev_table
            declared = sorted(ab.abbrev_decls.keys())
            print("count:", len(declared))
            unknown_codes = []
            for code in declared:
                decl = ab.get_abbrev(code)
                if decl.decl_tag is None:
                    unknown_codes.append((code, decl))
            print("abbrev codes with None tag:", len(unknown_codes))
            for code, decl in unknown_codes[:20]:
                print(f"  code={code} tag={decl.decl_tag} has_children={decl.has_children}")
                break

            dies = list(cu.iter_DIEs())
            nones = [d for d in dies if d.tag is None]
            print(f"\nNone-tag DIEs: {len(nones)}")
            d0 = nones[0]
            print("first None DIE:", d0.offset, "abbrev_code=", getattr(d0, 'abbrev_code', '?'))
            print("attrs:", list(d0.attributes.keys())[:10])
            break


if __name__ == "__main__":
    main()
