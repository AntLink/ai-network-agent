import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN

ELF_PATH = r'C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsd.elf'
f = open(ELF_PATH, 'rb')
elf = ELFFile(f)

ta = td = None
syms = {}
for sec in elf.iter_sections():
    if sec.name == '.text':
        ta, td = sec.header.sh_addr, sec.data()
    if sec.header.sh_type == 'SHT_SYMTAB':
        for sym in sec.iter_symbols():
            if sym['st_info']['type'] == 'STT_FUNC' and sym['st_value']:
                syms[sym.name] = (sym['st_value'], sym['st_size'])

print('=== Checking SSmsMsg structure fields ===')
for n, (va, sz) in sorted(syms.items(), key=lambda kv: kv[1][0]):
    if 'SSmsMsg' in n:
        print(f'  {n} @ 0x{va:08x} size={sz}')

print()
print('=== Checking relevant rodata strings (version) ===')
for sec in elf.iter_sections():
    if sec.name != '.rodata':
        continue
    data = sec.data()
    base = sec.header.sh_addr
    for pattern in [b'version', b'Version', b'v', b'VER']:
        i = data.find(pattern)
        while i != -1:
            s = max(0, i - 50)
            e = min(len(data), i + 50)
            chunk = data[s:e]
            null1 = chunk.find(b'\x00')
            if null1 != -1:
                s2 = null1 + s + 1
                null2 = chunk.find(b'\x00', s2)
                if null2 != -1:
                    full = chunk[s:null2+s].decode('ascii', 'replace')
                    if len(full) > 3 and len(full) < 80:
                        print(f'  @0x{base+s:08x}: "{full}"')
            i = data.find(pattern, i + 1)