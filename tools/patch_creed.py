#!/usr/bin/env python3
"""The Creed (1999) - Unofficial Patch v1.4 - by Andromeda Kiwi + Claude

Rebuilds the patched Creed.exe from an original Creed.exe v1.6 build 160.
Usage:  python patch_creed.py <original Creed.exe> [output.exe]

Only the Python standard library is needed. Every record is verified against
the original bytes, and the result is checked against the expected MD5.
See docs/TECHNICAL.md for what each change does.
"""
import hashlib
import sys

MD5_ORIGINAL = '746dfe681c5b157dbd53c3cd18d336c5'
MD5_PATCHED = 'c8e4a51c772495cd13ca5811a0536552'

# (file offset, original bytes, patched bytes)
RECORDS = [
    # PE header: TimeDateStamp +1 (release build identity)
    (0x00088, '5cca9236',
              '5dca9236'),
    # PE header: .text VirtualSize 0x872C6 -> 0x87400 (maps the code caves at the end of .text)
    (0x00180, 'c672',
              '0074'),
    # VA 0x00405CF0: CD drive search -> jmp CD cave (hybrid No-CD)
    (0x050F0, '81ec0c0200',
              'e933260800'),
    # VA 0x00405FC2: DirectInput keyboard SetCooperativeLevel 9 (EXCLUSIVE|BACKGROUND) -> 0xA (NONEXCLUSIVE|BACKGROUND)
    (0x053C2, '09',
              '0a'),
    # VA 0x00406D15: background buffer caps 0x1800 (SYSTEMMEMORY|TEXTURE) -> 0x2840 (OFFSCREENPLAIN|SYSTEMMEMORY|3DDEVICE)
    (0x06115, '0018',
              '4028'),
    # VA 0x00425670: dirty-rect restore function entry -> jmp CLIP cave + NOPs
    (0x24A70, 'a1ec6e4f0081ecec000000',
              'e95b2c0600909090909090'),
    # VA 0x0042A205: focus pause: enter while [0x4F8F00] (inactive) != 0, instead of TestCooperativeLevel
    (0x29605, 'a1086a4f00508b10ff526885c00f8488000000',
              '833d008f4f00000f848e000000909090909090'),
    # VA 0x0042A254: focus pause: leave when [0x4F8F00] == 0, call MOUSE cave, then original restore/reload
    (0x29654, 'a1086a4f00508b08ff516885c075bb',
              '833d008f4f000075c1e862e1050090'),
    # VA 0x0043C3FA: WndProc -> jmp WND cave
    (0x3B7FA, '83fe107724',
              'e9a5bf0400'),
    # VA 0x0043C7D1: after the registry read -> jmp REG cave + NOPs
    (0x3BBD1, '8b4c24246880000000',
              'e9aebb040090909090'),
    # VA 0x004882D0: CLIP cave - clip every dirty rect at 0x4B689C to 0..640 x 0..480 in place
    (0x876D0, '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
              '0fb70d98684b00ba9c684b0031c085c9743439027d0289023942047d03894204817a08800200007e07c7420880020000817a0ce00100007e07c7420ce001000083c21049ebc8a1ec6e4f0081ecec000000e955d3f9ff0000'),
    # VA 0x00488328: CD cave - use cd1\ / cd2\ if cd?\Data\data.v00|Data.v01 opens, else original drive search
    (0x87728, '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
              'bad8834800803d68534f00027505baea834800526a0068800000006a036a006a01680000008052ff1508944f0083f8ff741d50ff1510944f005a8b0a890d68524f00c6056c524f0000b801000000c35a81ec0c020000e973d9f7ff00'),
    # VA 0x00488384: REG cave - [0x4F7234]=1, [0x4F5368]=1, replaced instructions, jmp 0x0043C7DA
    (0x87784, '0000000000000000000000000000000000000000000000000000000000000000',
              'c70534724f0001000000c60568534f00018b4c24246880000000e93744fbff00'),
    # VA 0x004883A4: WND cave - on WM_ACTIVATEAPP store [0x4F8F00] = !wParam, continue WndProc
    (0x877A4, '0000000000000000000000000000000000000000000000000000000000000000',
              '83fe1c750c31c085ff0f94c0a3008f4f0083fe100f876540fbffe93c40fbff00'),
    # VA 0x004883C4: MOUSE cave - one GetDeviceState on the mouse to drop movement accumulated while paused
    (0x877C4, '0000000000000000000000000000000000000000',
              'a1fc694f0068f07b4e006a10508b08ff5124c300'),
    # VA 0x004883D8: strings "cd1\Data\data.v00", "cd2\Data\Data.v01"
    (0x877D8, '000000000000000000000000000000000000000000000000000000000000000000000000',
              '6364315c446174615c646174612e763030006364325c446174615c446174612e76303100'),
]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else src.rsplit('.', 1)[0] + '_patched.exe'
    data = bytearray(open(src, 'rb').read())
    md5 = hashlib.md5(data).hexdigest()
    if md5 == MD5_PATCHED:
        sys.exit('This Creed.exe is already patched (v1.4).')
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
