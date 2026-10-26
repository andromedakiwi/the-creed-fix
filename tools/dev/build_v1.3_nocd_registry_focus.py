"""Development script: builds Creed.exe v1.3 from the v1.0 output (fixes):
registry independence + hybrid No-CD (as v1.2) + focus-loss / Alt+Tab fix.
Usage: python build_v1.3_nocd_registry_focus.py <v1.0 Creed.exe> <out.exe>
Requires: pip install keystone-engine capstone."""
import keystone, capstone, hashlib, sys
SRC, OUT = sys.argv[1], sys.argv[2]
d = bytearray(open(SRC, 'rb').read())
assert hashlib.md5(d).hexdigest() == '16fd856cd481c6a933c6559c63da0262', 'needs v1.0 patched exe'
off = lambda va: va - 0x400000 - 0x1000 + 0x400
ks = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_32)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
asm = lambda src, va: bytes(ks.asm(src, va)[0])

INACTIVE = 0x4f8f00            # dword in the zero tail of .data (VirtualSize ends 0x4f86d0, page ends 0x4f9000)
CAVE_CD, CAVE_REG, CAVE_WND = 0x488310, 0x488378, 0x488398
S1, S2, T1, T2 = 0x4883b8, 0x4883c0, 0x4883c8, 0x4883dc
strings = {S1: b'cd1\\\0', S2: b'cd2\\\0', T1: b'cd1\\Data\\data.v00\0', T2: b'cd2\\Data\\Data.v01\0'}

caves = {
CAVE_CD: f"""
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
""",
CAVE_REG: """
 mov dword ptr [0x4f7234], 1
 mov byte ptr [0x4f5368], 1
 mov ecx, dword ptr [esp+0x24]
 push 0x80
 jmp 0x43c7da
""",
# WndProc: remember WM_ACTIVATEAPP state (edi = wParam, esi = msg)
CAVE_WND: f"""
 cmp esi, 0x1c
 jne w1
 xor eax, eax
 test edi, edi
 sete al
 mov dword ptr [{INACTIVE:#x}], eax
w1: cmp esi, 0x10
 ja 0x43c423
 jmp 0x43c3ff
""",
}
ends = {}
for va, src in caves.items():
    b = asm(src, va); ends[va] = va + len(b)
    o = off(va); assert d[o:o+len(b)] == bytes(len(b)), hex(va); d[o:o+len(b)] = b
for va, s in strings.items():
    o = off(va); assert d[o:o+len(s)] == bytes(len(s)); d[o:o+len(s)] = s
assert ends[CAVE_CD] <= CAVE_REG and ends[CAVE_REG] <= CAVE_WND and ends[CAVE_WND] <= S1, {hex(k): hex(v) for k, v in ends.items()}
assert T2 + len(strings[T2]) <= 0x488400

def hook(va, orig_hex, src, total):
    o = off(va); assert d[o:o+total] == bytes.fromhex(orig_hex), (hex(va), d[o:o+total].hex())
    b = asm(src, va); assert len(b) <= total
    d[o:o+total] = b + b'\x90' * (total - len(b))

hook(0x405cf0, '81ec0c0200', f'jmp {CAVE_CD:#x}', 5)                       # No-CD
hook(0x43c7d1, '8b4c24246880000000', f'jmp {CAVE_REG:#x}', 9)               # registry independence
hook(0x43c3fa, '83fe107724', f'jmp {CAVE_WND:#x}', 5)                       # WndProc: WM_ACTIVATEAPP
# pause loop: pause while inactive instead of while TestCooperativeLevel fails
hook(0x42a205, 'a1086a4f00508b10ff526885c00f8488000000',
     f'cmp dword ptr [{INACTIVE:#x}], 0\n je 0x42a2a0', 19)
hook(0x42a254, 'a1086a4f00508b08ff516885c075bb',
     f'cmp dword ptr [{INACTIVE:#x}], 0\n jne 0x42a21e', 15)
# DirectInput keyboard: EXCLUSIVE|BACKGROUND (9) -> NONEXCLUSIVE|BACKGROUND (0xA)
o = off(0x405fc1); assert d[o:o+2] == bytes.fromhex('6a09'); d[o+1] = 0x0a

open(OUT, 'wb').write(d)
def dis(va, n):
    for i in md.disasm(bytes(d[off(va):off(va)+n]), va): print(f'  {i.address:08x}: {i.mnemonic} {i.op_str}')
for va, n in ((0x405cf0, 6), (0x405fc1, 2), (0x42a205, 19), (0x42a254, 15), (0x43c3fa, 5), (0x43c7d1, 9)):
    print(hex(va)); dis(va, n)
for va in caves: print('cave', hex(va)); dis(va, ends[va] - va)
print(OUT, hashlib.md5(d).hexdigest())
