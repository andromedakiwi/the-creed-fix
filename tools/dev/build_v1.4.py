"""Development script: builds Creed.exe v1.4 directly from the ORIGINAL Creed.exe v1.6 build 160.
Fixes: background caps, dirty-rect clipping (colour + depth), registry independence, hybrid No-CD,
focus-loss pause via WM_ACTIVATEAPP, non-exclusive keyboard, mouse delta flush on resume.
Usage: python tools/dev/build_v1.4.py <original Creed.exe> <out.exe>      Requires: pip install keystone-engine capstone"""
import keystone, capstone, hashlib, sys
SRC, OUT = sys.argv[1], sys.argv[2]
d = bytearray(open(SRC, 'rb').read())
assert hashlib.md5(d).hexdigest() == '746dfe681c5b157dbd53c3cd18d336c5', 'needs the original Creed.exe v1.6 build 160'
off = lambda va: va - 0x400000 - 0x1000 + 0x400
ks = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_32)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
asm = lambda src, va: bytes(ks.asm(src, va)[0])

INACTIVE = 0x4f8f00          # dword in the zero tail of the .data page (VirtualSize ends 0x4f86d0)
CAVE_START, CAVE_END = 0x4882d0, 0x488400

# --- PE: .text VirtualSize 0x872C6 -> 0x87400 so the caves are mapped
o = 0x180; assert d[o:o+4] == bytes.fromhex('c6720800'); d[o:o+4] = (0x87400).to_bytes(4, 'little')
# --- Fix 1: background buffer caps 0x1800 -> 0x2840
o = off(0x406d15); assert d[o:o+4] == bytes.fromhex('00180000'); d[o:o+4] = bytes.fromhex('40280000')
# --- keyboard SetCooperativeLevel 9 -> 0xA
o = off(0x405fc2); assert d[o] == 9; d[o] = 0x0a

T1, T2 = 'T1', 'T2'   # placeholders resolved after layout
caves = [
('CLIP', """
 movzx ecx, word ptr [0x4b6898]
 mov edx, 0x4b689c
 xor eax, eax
c0: test ecx, ecx
 je c9
 cmp dword ptr [edx], eax
 jge c1
 mov dword ptr [edx], eax
c1: cmp dword ptr [edx+4], eax
 jge c2
 mov dword ptr [edx+4], eax
c2: cmp dword ptr [edx+8], 0x280
 jle c3
 mov dword ptr [edx+8], 0x280
c3: cmp dword ptr [edx+0xc], 0x1e0
 jle c4
 mov dword ptr [edx+0xc], 0x1e0
c4: add edx, 0x10
 dec ecx
 jmp c0
c9: mov eax, dword ptr [0x4f6eec]
 sub esp, 0xec
 jmp 0x42567b
"""),
('CD', """
 mov edx, {T1}
 cmp byte ptr [0x4f5368], 2
 jne l1
 mov edx, {T2}
l1: push edx
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
 pop edx
 mov ecx, dword ptr [edx]
 mov dword ptr [0x4f5268], ecx
 mov byte ptr [0x4f526c], 0
 mov eax, 1
 ret
nofiles: pop edx
 sub esp, 0x20c
 jmp 0x405cf6
"""),
('REG', """
 mov dword ptr [0x4f7234], 1
 mov byte ptr [0x4f5368], 1
 mov ecx, dword ptr [esp+0x24]
 push 0x80
 jmp 0x43c7da
"""),
('WND', f"""
 cmp esi, 0x1c
 jne w1
 xor eax, eax
 test edi, edi
 sete al
 mov dword ptr [{INACTIVE:#x}], eax
w1: cmp esi, 0x10
 ja 0x43c423
 jmp 0x43c3ff
"""),
('MOUSE', """
 mov eax, dword ptr [0x4f69fc]
 push 0x4e7bf0
 push 0x10
 push eax
 mov ecx, dword ptr [eax]
 call dword ptr [ecx+0x24]
 ret
"""),
]
strings = [('T1', b'cd1\\Data\\data.v00\0'), ('T2', b'cd2\\Data\\Data.v01\0')]

# layout: code caves first (16-byte aligned), strings at the end
addr = {}
va = CAVE_START
sizes = {}
for name, src in caves:   # first pass with dummy string addresses to get sizes
    sizes[name] = len(asm(src.format(T1='0x488300', T2='0x488300'), 0x488300))
for name, _ in caves:
    addr[name] = va; va = (va + sizes[name] + 3) & ~3
for name, s in strings:
    addr[name] = va; va += len(s)
assert va <= CAVE_END, f'caves overflow: end {va:#x}'
for name, src in caves:
    b = asm(src.format(T1=f"{addr['T1']:#x}", T2=f"{addr['T2']:#x}"), addr[name])
    assert len(b) == sizes[name]
    o = off(addr[name]); assert d[o:o+len(b)] == bytes(len(b)); d[o:o+len(b)] = b
for name, s in strings:
    o = off(addr[name]); assert d[o:o+len(s)] == bytes(len(s)); d[o:o+len(s)] = s

def hook(va, orig_hex, src, total):
    o = off(va); assert d[o:o+total] == bytes.fromhex(orig_hex), (hex(va), d[o:o+total].hex())
    b = asm(src, va); assert len(b) <= total, (hex(va), len(b))
    d[o:o+total] = b + b'\x90' * (total - len(b))

hook(0x425670, 'a1ec6e4f0081ecec000000', f"jmp {addr['CLIP']:#x}", 11)        # clip dirty rects in place
hook(0x405cf0, '81ec0c0200', f"jmp {addr['CD']:#x}", 5)                         # hybrid No-CD
hook(0x43c7d1, '8b4c24246880000000', f"jmp {addr['REG']:#x}", 9)               # registry independence
hook(0x43c3fa, '83fe107724', f"jmp {addr['WND']:#x}", 5)                       # WM_ACTIVATEAPP
hook(0x42a205, 'a1086a4f00508b10ff526885c00f8488000000',
     f"cmp dword ptr [{INACTIVE:#x}], 0\n je 0x42a2a0", 19)                     # pause while inactive
hook(0x42a254, 'a1086a4f00508b08ff516885c075bb',
     f"cmp dword ptr [{INACTIVE:#x}], 0\n jne 0x42a21e\n call {addr['MOUSE']:#x}", 15)  # resume + flush mouse

# PE TimeDateStamp + 1: the released build (a fresh hash after Smart App Control blocked the first one)
import struct
ts_off = 0x80 + 4 + 4   # e_lfanew is 0x80: 'PE\0\0' + Machine/NumberOfSections -> TimeDateStamp
assert struct.unpack_from('<I', d, 0x3c)[0] == 0x80
assert struct.unpack_from('<I', d, ts_off)[0] == 0x3692ca5c
struct.pack_into('<I', d, ts_off, 0x3692ca5d)
open(OUT, 'wb').write(d)
def dis(va, n):
    for i in md.disasm(bytes(d[off(va):off(va)+n]), va): print(f'  {i.address:08x}: {i.mnemonic} {i.op_str}')
for va, n in ((0x425670, 11), (0x405cf0, 5), (0x43c7d1, 9), (0x43c3fa, 5), (0x42a205, 19), (0x42a254, 15)):
    print(hex(va)); dis(va, n)
for name, _ in caves: print('cave', name, hex(addr[name])); dis(addr[name], sizes[name])
print({k: hex(v) for k, v in addr.items()}, 'end', hex(va))
print(OUT, hashlib.md5(d).hexdigest())
