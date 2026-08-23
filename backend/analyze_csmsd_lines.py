import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from elftools.elf.elffile import ELFFile

ELF_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf"


def main():
    with open(ELF_PATH, "rb") as f:
        elf = ELFFile(f)
        dw = elf.get_dwarf_info()

        # find CUs for MetricsNet.cpp / EquipCtrlNet.cpp and dump line programs
        # into sorted (addr -> file:line) tables
        targets = {}
        want_files = ["MetricsNet.cpp", "EquipCtrlNet.cpp"]

        for cu in dw.iter_CUs():
            top = cu.get_top_DIE()
            nattr = top.attributes.get("DW_AT_name")
            if not nattr:
                continue
            name = nattr.value.decode()
            base = name.split("/")[-1]
            if base not in want_files:
                continue

            lp = dw.line_program_for_CU(cu)
            header = lp.header
            findex = {}
            for i, fe in enumerate(header.file_entry):
                findex[i + 1] = fe.name.decode(errors="replace")

            rows = []
            for entry in lp.get_entries():
                st = entry.state
                if st is None or st.end_sequence:
                    continue
                fname = findex.get(st.file, "?")
                rows.append((st.address, fname, st.line))

            rows.sort()
            targets[base] = rows
            print(f"{name}: {len(rows)} line rows")

        # ---- find specific line hits -------------------------------------
        for base, rows in targets.items():
            print(f"\n=== {base} ===")

            def addr_for_line(line):
                hits = [r for r in rows if r[2] == line]
                return hits[:6]

            if base == "MetricsNet.cpp":
                for ln in (2670, 2671, 2672, 2673, 2674, 2675):
                    hs = addr_for_line(ln)
                    print(f"  line {ln}: {[hex(a) for a, _, _ in hs]}")

            if base == "EquipCtrlNet.cpp":
                # dump the address ranges covered to locate handlers later
                total = len(rows)
                print(f"  address span: 0x{rows[0][0]:08x} - 0x{rows[-1][0]:08x}")

        # save full tables for reuse
        import pickle
        with open(r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_line_tables.pkl", "wb") as g:
            pickle.dump(targets, g)
        print("\nsaved line tables")


if __name__ == "__main__":
    main()
