import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"

INTERESTING_CUS = ["EquipCtrlNet", "Task.cpp", "DfCtrlNet", "VCPCtrlNet", "Monitor",
                   "PersistentData", "PanTask", "OccupancyTask", "MeasurementTask",
                   "ScanDfTask", "AvdTask", "ProcessorNode", "Rds"]


def die_name(die):
    attr = die.attributes.get("DW_AT_name")
    return attr.value.decode() if attr else None


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        dw = elf.get_dwarf_info()

        results = []
        for cu in dw.iter_CUs():
            top = cu.get_top_DIE()
            cu_name = die_name(top) or ""
            if not any(k in cu_name for k in INTERESTING_CUS):
                continue

            # build map offset->die for reference resolution
            all_dies = list(cu.iter_DIEs())
            by_off = {d.offset: d for d in all_dies}

            # typedefs: name -> ref offset
            typedefs = {}
            for d in all_dies:
                if d.tag == "DW_TAG_typedef":
                    t = d.attributes.get("DW_AT_type")
                    n = die_name(d)
                    if n and t is not None:
                        typedefs.setdefault(t.value + cu.cu_offset, []).append(n)

            def scope_chain(die):
                """walk parents via DW_AT_specification / abstract_origin or hierarchy"""
                names = []
                d = die
                seen = set()
                while d is not None and d.offset not in seen:
                    seen.add(d.offset)
                    n = die_name(d)
                    if n:
                        names.append(n)
                    # parent: find DIE whose child is this one - expensive; use spec instead
                    spec = d.attributes.get("DW_AT_specification")
                    if spec is not None:
                        tgt = by_off.get(spec.value + cu.cu_offset)
                        if tgt is not None:
                            d = tgt
                            continue
                    break
                return names

            for d in all_dies:
                if d.tag != "DW_TAG_enumeration_type":
                    continue
                enumerators = []
                for c in d.iter_children():
                    if c.tag == "DW_TAG_enumerator":
                        cn = die_name(c)
                        cv = c.attributes.get("DW_AT_const_value")
                        if cn and cv is not None:
                            enumerators.append((cn, cv.value))
                if not enumerators:
                    continue
                n = die_name(d)
                if not n:
                    refs = typedefs.get(d.offset, [])
                    n = "typedef:" + ",".join(refs) if refs else "<anon>"
                results.append((cu_name, n, enumerators))

        print(f"collected {len(results)} enums")
        seen_keys = set()
        for cu_name, n, vals in results:
            key = tuple(sorted(vals))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            print(f"\n=== {n}   [{cu_name}] ({len(vals)} values)")
            show = sorted(vals, key=lambda x: x[1])
            for name, v in show[:80]:
                print(f"  {v:6d}  {name}")
            if len(show) > 80:
                print(f"  ... +{len(show)-80} more")


if __name__ == "__main__":
    main()
