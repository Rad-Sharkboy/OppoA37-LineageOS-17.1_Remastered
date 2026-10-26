#!/usr/bin/env python3
"""Build a pinned, reproducible AArch64 extension for the original V2 Power HAL.

No original ROM binary is committed. Input/output and compiler paths are explicit.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

ORIGINAL_SHA256 = '0acfe2bafdcffea00b492f9cd21932b5cf606bc49e0a29e69c64c401a555db15'
BASE = 0x8000
STATE = 0x70c0

def run(*args):
    return subprocess.check_output([str(x) for x in args], text=True)

def branch(start, end):
    distance = end - start
    if distance % 4 or not -(1 << 27) <= distance < (1 << 27):
        raise ValueError('AArch64 branch out of range/alignment')
    return struct.pack('<I', 0x14000000 | ((distance // 4) & 0x3ffffff))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--cross-prefix', required=True)
    args = parser.parse_args()
    original = args.original.read_bytes()
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA256:
        raise SystemExit('Original Power HAL hash mismatch; refusing to patch.')
    if original[0x4840:0x4844] != bytes.fromhex('ff4301d1') or original[0x4b70:0x4b74] != bytes.fromhex('ff8302d1'):
        raise SystemExit('Original function prologue mismatch.')
    if original[:6] != b'\x7fELF\x02\x01' or struct.unpack_from('<H', original, 18)[0] != 183:
        raise SystemExit('Expected little-endian AArch64 ELF64.')
    args.output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parent
    prefix = args.cross_prefix
    disassembly = run(prefix + 'objdump', '-d', args.original)
    match = re.search(r'^([0-9a-f]+) <dlsym@plt>:', disassembly, re.M)
    if not match:
        raise SystemExit('Cannot locate original dlsym PLT entry.')
    dlsym = int(match[1], 16)
    linker = args.output / 'bridge.ld'
    linker.write_text(f'''ENTRY(a37_hint)
PHDRS {{ code PT_LOAD FLAGS(5); }}
SECTIONS {{
 . = {BASE};
 .text : {{ *(.text .text.*) *(.rodata .rodata.*) }} :code
 .got : {{ *(.got .got.*) }} :code
 .data : {{ *(.data .data.*) }} :code
 .bss : {{ *(.bss .bss.*) }} :code
 ASSERT(SIZEOF(.got) == 0, "Unexpected GOT")
 ASSERT(SIZEOF(.data) == 0, "Unexpected data")
 ASSERT(SIZEOF(.bss) == 0, "Unexpected BSS")
 /DISCARD/ : {{ *(.comment) *(.note*) *(.eh_frame*) }}
}}
original_hint_tail = 0x4844;
original_interactive_tail = 0x4b74;
original_dlsym = {dlsym};
a37_state = {STATE};
''')
    common = ['-Os', '-ffreestanding', '-fno-builtin', '-fno-stack-protector',
              '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-fPIC',
              '-fno-tree-loop-distribute-patterns', '-fvisibility=hidden',
              '-mgeneral-regs-only', '-Wall', '-Wextra', '-Werror', '-c']
    run(prefix + 'gcc', *common, root / 'bridge.c', '-o', args.output / 'bridge.o')
    run(prefix + 'gcc', '-c', root / 'trampolines.S', '-o', args.output / 'trampolines.o')
    elf = args.output / 'bridge.elf'
    run(prefix + 'ld', '--build-id=none', '-T', linker, args.output / 'bridge.o',
        args.output / 'trampolines.o', '-o', elf)
    undefined = run(prefix + 'nm', '-u', elf).strip()
    if undefined:
        raise SystemExit('Unresolved extension symbols: ' + undefined)
    blob_path = args.output / 'bridge.bin'
    run(prefix + 'objcopy', '-O', 'binary', '--only-section=.text', elf, blob_path)
    blob = blob_path.read_bytes()
    if len(blob) > 4096:
        raise SystemExit('Extension exceeds the reserved 4 KiB code budget.')
    symbols = {}
    for line in run(prefix + 'nm', elf).splitlines():
        fields = line.split()
        if len(fields) == 3:
            symbols[fields[2]] = int(fields[0], 16)
    patches = [(0x4840, branch(0x4840, symbols['a37_hint'])),
               (0x4b70, branch(0x4b70, symbols['a37_interactive']))]
    phoff = struct.unpack_from('<Q', original, 32)[0]
    phsize, phcount = struct.unpack_from('<HH', original, 54)
    if (phoff, phsize, phcount) != (64, 56, 10):
        raise SystemExit('Unexpected program-header layout.')
    note_index = 9
    note = struct.unpack_from('<IIQQQQQQ', original, phoff + note_index * phsize)
    if note[0] != 4 or note[2] != 0x288:
        raise SystemExit('Unexpected NOTE program header.')
    # Notes remain covered by the first original LOAD and by section headers.
    # Reuse only their redundant PT_NOTE descriptor for an appended R-X LOAD.
    new_load = struct.pack('<IIQQQQQQ', 1, 5, BASE, BASE, BASE, len(blob), len(blob), 4096)
    patches.append((phoff + note_index * phsize, new_load))
    rw_offset = phoff + 4 * phsize
    rw = struct.unpack_from('<IIQQQQQQ', original, rw_offset)
    if rw[:4] != (1, 6, 0x5000, 0x5000) or rw[6] != 0x20b1:
        raise SystemExit('Unexpected writable segment.')
    # 16-byte state sits in the already-mapped last BSS page. Extend p_memsz,
    # with no executable writable segment and no new background thread.
    patches.append((rw_offset + 40, struct.pack('<Q', STATE + 16 - rw[3])))
    # Give the modified image a distinct build ID while leaving Android's
    # API-identification note intact. The original binary uses a 16-byte ID.
    build_id = bytes.fromhex('ed0cc3619db77cd26c1cd78212529d96')
    build_id_offset = original.index(build_id)
    if not 0x288 <= build_id_offset < 0x2c0:
        raise SystemExit('Unexpected build ID location.')
    patches.append((build_id_offset, hashlib.sha256(blob + original).digest()[:16]))
    patched = bytearray(original)
    patched.extend(bytes(BASE - len(patched)))
    patched.extend(blob)
    for offset, data in patches:
        patched[offset:offset + len(data)] = data
    output = args.output / 'android.hardware.power@1.2-service-qti'
    output.write_bytes(patched)
    metadata = {'original_sha256': ORIGINAL_SHA256, 'patched_sha256': hashlib.sha256(patched).hexdigest(),
                'blob_sha256': hashlib.sha256(blob).hexdigest(), 'blob_offset': BASE,
                'blob_size': len(blob), 'original_size': len(original), 'patched_size': len(patched),
                'patches': [{'offset': offset, 'hex': data.hex()} for offset, data in patches],
                'symbols': symbols}
    (args.output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    lines = ['#!/system/bin/sh', '# Generated by build.py; the exact original V2 hash is mandatory.',
             f"A37_ORIGINAL_SHA256='{ORIGINAL_SHA256}'",
             f"A37_PATCHED_SHA256='{metadata['patched_sha256']}'", 'a37_patch_hal() {',
             '    [ "$(sha256sum "$1" | cut -d\' \' -f1)" = "$A37_ORIGINAL_SHA256" ] || return 1',
             '    cp "$1" "$2"']
    for offset, data in patches + [(BASE, blob)]:
        encoded = base64.b64encode(data).decode('ascii')
        lines.append(f'    printf \'%s\' \'{encoded}\' | base64 -d | dd of="$2" bs=1 seek={offset} conv=notrunc 2>/dev/null')
    lines.extend(['    [ "$(sha256sum "$2" | cut -d\' \' -f1)" = "$A37_PATCHED_SHA256" ]', '}'])
    (args.output / 'payload.sh').write_text('\n'.join(lines) + '\n')
    print(json.dumps({key: value for key, value in metadata.items() if key not in ('symbols', 'patches')}, indent=2))

if __name__ == '__main__':
    main()
