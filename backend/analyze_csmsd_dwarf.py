import sys
from elftools.elf.elffile import ELFFile

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

WANT_ENUMS = ["EMsgType", "EErrorCode", "EErrStatus"]


def die_name(die):
    attr = die.attributes.get("DW_AT_name")
    return attr.value.decode() if attr else None


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        dw = elf.get_dwarf_info()

        found_enums = {}
        found_hdr = None

        for cu in dw.iter_CUs():
            for die in cu.iter_DIEs():
                if die.tag == "DW_TAG_enumeration_type":
                    n = die_name(die)
                    if n and any(w in n for w in WANT_ENUMS):
                        vals = []
                        for c in die.iter_children():
                            if c.tag == "DW_TAG_enumerator":
                                cn = die_name(c)
                                cv = c.attributes.get("DW_AT_const_value")
                                if cn and cv is not None:
                                    vals.append((cn, cv.value))
                        if n not in found_enums or len(vals) > len(found_enums[n]):
                            found_enums[n] = vals

                elif die.tag == "DW_TAG_structure_type" and found_hdr is None:
                    n = die_name(die)
                    if n == "SHdr":
                        members = []
                        size = die.attributes.get("DW_AT_byte_size")
                        for c in die.iter_children():
                            if c.tag == "DW_TAG_member":
                                mn = die_name(c)
                                loc = c.attributes.get("DW_AT_data_member_location")
                                members.append((mn, loc.value if loc else "?"))
                        if members:
                            found_hdr = (size.value if size else "?", members)

        print("=" * 78)
        print("  ENUMS")
        print("=" * 78)
        for n, vals in sorted(found_enums.items()):
            print(f"\n--- {n} ({len(vals)} values) ---")
            for name, v in sorted(vals, key=lambda x: x[1]):
                print(f"  {v:5d}  {name}")

        print("\n" + "=" * 78)
        print("  STRUCT SSmsMsg::SHdr")
        print("=" * 78)
        if found_hdr:
            size, members = found_hdr
            print(f"size = {size}")
            for mn, off in members:
                print(f"  +{off:<3} {mn}")
        else:
            print("SHdr not found by that name")


if __name__ == "__main__":
    main()
