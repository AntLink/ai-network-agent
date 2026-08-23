import sys

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
            n = die_name(top)
            print(f"v{cu.header.version} {cu.header.unit_length:>9} {n}")


if __name__ == "__main__":
    main()
