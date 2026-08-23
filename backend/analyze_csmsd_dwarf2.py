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

        # check raw strings first
        for sec in elf.iter_sections():
            if sec.name == ".debug_str":
                data = sec.data()
                for probe in [b"EMsgType\0", b"EErrorCode\0", b"SHdr\0", b"SGetPanResp"]:
                    i = data.find(probe)
                    print(f".debug_str {probe!r}: {'FOUND @' + str(i) if i >= 0 else 'missing'}")
                break

        enum_names = collections.Counter()
        struct_names = collections.Counter()
        cu_count = 0
        die_count = 0
        for cu in dw.iter_CUs():
            cu_count += 1
            try:
                for die in cu.iter_DIEs():
                    die_count += 1
                    n = die_name(die)
                    if not n:
                        continue
                    if die.tag == "DW_TAG_enumeration_type":
                        enum_names[n] += 1
                    elif die.tag == "DW_TAG_structure_type" or die.tag == "DW_TAG_class_type":
                        struct_names[n] += 1
            except Exception as e:
                print(f"CU error: {e}")

        print(f"\nCUs: {cu_count}, DIEs: {die_count}")
        print("\nENUM NAMES:")
        for n, c in sorted(enum_names.items()):
            print(f"  {n} x{c}")
        print("\nSTRUCT/CLASS containing 'SGet' or 'SHdr' or 'Msg':")
        for n, c in sorted(struct_names.items()):
            if any(k in n for k in ("SGet", "SHdr", "Msg", "SEquip")):
                print(f"  {n} x{c}")


if __name__ == "__main__":
    main()
