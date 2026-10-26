#!/usr/bin/env python3
"""The Creed (1999) - Unofficial Patch v1.3 - by Andromeda Kiwi + Claude

Rebuilds the patched Creed.exe from an original Creed.exe v1.6 build 160.
Usage:  python patch_creed.py <original Creed.exe> [output.exe]

Only the Python standard library is needed. Every record is verified against
the original bytes, and the result is checked against the expected MD5.
See docs/TECHNICAL.md for what each change does.
"""
import hashlib
import sys

MD5_ORIGINAL = '746dfe681c5b157dbd53c3cd18d336c5'
MD5_PATCHED = '80ba90515bea3d43ba223961cc63b150'

# (file offset, original bytes, patched bytes)
RECORDS = [
    # PE header: .text VirtualSize 0x872C6 -> 0x87400 (maps the code caves at the end of .text)
    (0x00180, 'c672',
              '0074'),
    # VA 0x00405CF0: CD drive search -> jmp 0x00488310 (hybrid No-CD cave)
    (0x050F0, '81ec0c0200',
              'e91b260800'),
    # VA 0x00405FC1: DirectInput keyboard SetCooperativeLevel 9 (EXCLUSIVE|BACKGROUND) -> 0xA (NONEXCLUSIVE|BACKGROUND)
    (0x053C1, '6a09',
              '6a0a'),
    # VA 0x00406D15: background buffer caps 0x1800 (SYSTEMMEMORY|TEXTURE) -> 0x2840 (OFFSCREENPLAIN|SYSTEMMEMORY|3DDEVICE)
    (0x06115, '0018',
              '4028'),
    # VA 0x004257FB: dirty-rect depth copy -> jmp 0x004882D0 (clipping cave) + NOPs
    (0x24BFB, '8ba8a0684b008b989c684b008b88a4684b008b80a8684b00',
              'e9d02a060090909090909090909090909090909090909090'),
    # VA 0x0042A205: focus-loss pause: enter while [0x4F8F00] (inactive) != 0, instead of TestCooperativeLevel
    (0x29605, 'a1086a4f00508b10ff526885c00f8488000000',
              '833d008f4f00000f848e000000909090909090'),
    # VA 0x0042A254: focus-loss pause: leave when [0x4F8F00] == 0, then original restore/reload
    (0x29654, 'a1086a4f00508b08ff516885c075bb',
              '833d008f4f000075c1909090909090'),
    # VA 0x0043C3FA: WndProc -> jmp 0x00488398 (WM_ACTIVATEAPP cave)
    (0x3B7FA, '83fe107724',
              'e999bf0400'),
    # VA 0x0043C7D1: after the registry read -> jmp 0x00488378 (registry-independence cave) + NOPs
    (0x3BBD1, '8b4c24246880000000',
              'e9a2bb040090909090'),
    # VA 0x004882D0: cave - clamp dirty rect to the depth surface size, jmp 0x00425813
    (0x876D0, '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
              '8ba8a0684b008b989c684b008b88a4684b008b80a8684b0085db7d0231db85ed7d0231ed3b4c24307e048b4c24303b44242c7e048b44242ce906d5f9ff'),
    # VA 0x00488310: cave - hybrid No-CD (use cd1\ / cd2\ if the data file opens, else original drive search)
    (0x87710, '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
              'b8b8834800bac8834800803d68534f0002750ab8c0834800badc834800506a0068800000006a036a006a01680000008052ff1508944f0083f8ff741d50ff1510944f00588b08890d68524f00c6056c524f0000b801000000c35881ec0c020000e981d9f7ff00'),
    # VA 0x00488378: cave - [0x4F7234]=1, [0x4F5368]=1, replaced instructions, jmp 0x0043C7DA
    (0x87778, '00000000000000000000000000000000000000000000000000000000000000',
              'c70534724f0001000000c60568534f00018b4c24246880000000e94344fbff'),
    # VA 0x00488398: cave - on WM_ACTIVATEAPP store [0x4F8F00] = !wParam, continue WndProc
    (0x87798, '00000000000000000000000000000000000000000000000000000000000000',
              '83fe1c750c31c085ff0f94c0a3008f4f0083fe100f877140fbffe94840fbff'),
    # VA 0x004883B8: strings "cd1\", "cd2\", "cd1\Data\data.v00", "cd2\Data\Data.v01"
    (0x877B8, '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
              '6364315c000000006364325c000000006364315c446174615c646174612e7630300000006364325c446174615c446174612e76303100'),
]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else src.rsplit('.', 1)[0] + '_patched.exe'
    data = bytearray(open(src, 'rb').read())
    md5 = hashlib.md5(data).hexdigest()
    if md5 == MD5_PATCHED:
        sys.exit('This Creed.exe is already patched (v1.3).')
    if md5 != MD5_ORIGINAL:
        sys.exit(f'Unknown Creed.exe (MD5 {md5}); expected v1.6 build 160 ({MD5_ORIGINAL}).')
    for off, old, new in RECORDS:
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        if data[off:off + len(old)] != old:
            sys.exit(f'Unexpected bytes at 0x{off:X} - nothing written.')
        data[off:off + len(new)] = new
    if hashlib.md5(data).hexdigest() != MD5_PATCHED:
        sys.exit('Result does not match the expected MD5 - nothing written.')
    open(out, 'wb').write(data)
    print(f'Patched Creed.exe written to {out}')


if __name__ == '__main__':
    main()
