"""Development script: assembles the v1.0 fixes (background caps + dirty-rect clipping cave)
with keystone. Usage: python build_v1.0_fixes.py <original Creed.exe> <out.exe>
Requires: pip install pefile keystone-engine capstone. Use tools/patch_creed.py for normal patching."""
import pefile, keystone, capstone, hashlib, sys
SRC, OUT = sys.argv[1], sys.argv[2]
d = bytearray(open(SRC,'rb').read())
assert hashlib.md5(d).hexdigest()=='746dfe681c5b157dbd53c3cd18d336c5'
p = pefile.PE(data=bytes(d)); base=0x400000
off = lambda va: p.get_offset_from_rva(va-base)
ks = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_32)
# Patch 1: background surface caps 0x1800 -> 0x2840
o=off(0x406d0e); assert d[o:o+11]==bytes.fromhex('c784248400000000180000'); d[o+7:o+11]=(0x2840).to_bytes(4,'little')
# Patch 2: clip dirty rects to the depth surface size before memcpy
HOOK, RET, CAVE = 0x4257fb, 0x425813, 0x4882d0
o=off(HOOK); assert d[o:o+24]==bytes.fromhex('8ba8a0684b008b989c684b008b88a4684b008b80a8684b00')
cave_asm = f"""
 mov ebp, dword ptr [eax+0x4b68a0]
 mov ebx, dword ptr [eax+0x4b689c]
 mov ecx, dword ptr [eax+0x4b68a4]
 mov eax, dword ptr [eax+0x4b68a8]
 test ebx, ebx
 jge l1
 xor ebx, ebx
l1: test ebp, ebp
 jge l2
 xor ebp, ebp
l2: cmp ecx, dword ptr [esp+0x30]
 jle l3
 mov ecx, dword ptr [esp+0x30]
l3: cmp eax, dword ptr [esp+0x2c]
 jle l4
 mov eax, dword ptr [esp+0x2c]
l4: jmp {RET:#x}
"""
cave,_ = ks.asm(cave_asm, CAVE); cave=bytes(cave)
co=off(CAVE); assert d[co:co+len(cave)]==bytes(len(cave)), 'cave not empty'
d[co:co+len(cave)]=cave
jmp,_=ks.asm(f"jmp {CAVE:#x}", HOOK); jmp=bytes(jmp)
d[o:o+24]=jmp+b'\x90'*(24-len(jmp))
# extend .text VirtualSize so the cave is inside the mapped section
t=p.sections[0]; vs_off=t.get_file_offset()+8
d[vs_off:vs_off+4]=(t.SizeOfRawData).to_bytes(4,'little')
open(OUT,'wb').write(d)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
for i in md.disasm(bytes(d[o:o+8]),HOOK): print(f'{i.address:08x}: {i.mnemonic} {i.op_str}')
print('--cave')
for i in md.disasm(cave,CAVE): print(f'{i.address:08x}: {i.mnemonic} {i.op_str}')
print(OUT, hashlib.md5(d).hexdigest())
