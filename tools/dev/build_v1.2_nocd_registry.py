"""Development script: builds Creed.exe v1.2 from the v1.0 output (fixes) by adding the
registry-independence and hybrid No-CD code caves, assembled with keystone.
Usage: python build_v1.2_nocd_registry.py <v1.0 Creed.exe> <out.exe>
Requires: pip install keystone-engine capstone. Use tools/patch_creed.py for normal patching."""
import keystone, capstone, hashlib, sys
SRC, OUT = sys.argv[1], sys.argv[2]
d = bytearray(open(SRC,'rb').read())
assert hashlib.md5(d).hexdigest()=='16fd856cd481c6a933c6559c63da0262', 'needs v1.0 patched exe'
off = lambda va: va - 0x400000 - 0x1000 + 0x400
ks = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_32)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
CAVE_CD, CAVE_REG = 0x488320, 0x488390
S1, S2, T1, T2 = 0x4883c0, 0x4883c8, 0x4883d0, 0x4883e8
strings = {S1: b'cd1\\\0', S2: b'cd2\\\0', T1: b'cd1\\Data\\data.v00\0', T2: b'cd2\\Data\\Data.v01\0'}
cave_cd = f"""
 mov eax, {S1:#x}
 mov edx, {T1:#x}
 cmp byte ptr [0x4f5368], 2
 jne l1
 mov eax, {S2:#x}
 mov edx, {T2:#x}
l1: push eax
 push 0
 push 0x80
 push 3
 push 0
 push 1
 push 0x80000000
 push edx
 call dword ptr [0x4f9408]
 cmp eax, -1
 je nofiles
 push eax
 call dword ptr [0x4f9410]
 pop eax
 mov ecx, dword ptr [eax]
 mov dword ptr [0x4f5268], ecx
 mov byte ptr [0x4f526c], 0
 mov eax, 1
 ret
nofiles: pop eax
 sub esp, 0x20c
 jmp 0x405cf6
"""
cave_reg = """
 mov dword ptr [0x4f7234], 1
 mov byte ptr [0x4f5368], 1
 mov ecx, dword ptr [esp+0x24]
 push 0x80
 jmp 0x43c7da
"""
b_cd = bytes(ks.asm(cave_cd, CAVE_CD)[0]); b_reg = bytes(ks.asm(cave_reg, CAVE_REG)[0])
assert CAVE_CD + len(b_cd) <= CAVE_REG and CAVE_REG + len(b_reg) <= S1, (len(b_cd), len(b_reg))
for va, blob in [(CAVE_CD, b_cd), (CAVE_REG, b_reg)] + list(strings.items()):
    o = off(va); assert d[o:o+len(blob)] == bytes(len(blob)), hex(va); d[o:o+len(blob)] = blob
assert max(off(k)+len(v) for k,v in strings.items()) <= off(0x488400)
# hooks
o = off(0x405cf0); assert d[o:o+6] == bytes.fromhex('81ec0c020000')
d[o:o+5] = bytes(ks.asm(f"jmp {CAVE_CD:#x}", 0x405cf0)[0])
o = off(0x43c7d1); assert d[o:o+9] == bytes.fromhex('8b4c24246880000000')
d[o:o+9] = bytes(ks.asm(f"jmp {CAVE_REG:#x}", 0x43c7d1)[0]) + b'\x90'*4
open(OUT,'wb').write(d)
for va,n in ((0x405cf0,6),(0x43c7d1,9)):
    for i in md.disasm(bytes(d[off(va):off(va)+n]), va): print(f'{i.address:08x}: {i.mnemonic} {i.op_str}')
print('-- cave_cd'); [print(f'{i.address:08x}: {i.mnemonic} {i.op_str}') for i in md.disasm(b_cd, CAVE_CD)]
print('-- cave_reg'); [print(f'{i.address:08x}: {i.mnemonic} {i.op_str}') for i in md.disasm(b_reg, CAVE_REG)]
print(OUT, hashlib.md5(d).hexdigest())
