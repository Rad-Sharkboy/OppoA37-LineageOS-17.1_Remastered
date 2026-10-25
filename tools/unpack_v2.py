#!/usr/bin/env python3
"""Reconstruct the pinned V2 release without mounting or altering its image.

Requires curl, brotli and debugfs on PATH. Output directory must not exist.
The ext4 image is authoritative for Android owners, labels, xattrs and links.
The extracted tree is an inspection/editing copy, not a ready-to-flash filesystem.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import zipfile

URL = 'https://github.com/Rad-Sharkboy/OppoA37-LineageOS-17.1_Remastered/releases/download/V2/Lineage_17.1_REMASTERED_V2.zip'
SHA256 = '446958b5e5ba36b23db6edc6f20caddfd5c0f01f0fb9ce26c294ffd82aa9ed9e'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def reconstruct(root):
    lines = (root / 'system.transfer.list').read_text().splitlines()
    if lines[0] != '4':
        raise ValueError('Expected transfer-list version 4')
    ops = []
    for line in lines[4:]:
        cmd, ranges = line.split()
        values = list(map(int, ranges.split(',')))
        if cmd not in ('new', 'zero', 'erase') or values[0] != len(values) - 1 or values[0] % 2:
            raise ValueError('Unsupported operation/ranges: ' + line)
        for start, end in zip(values[1::2], values[2::2]):
            if not 0 <= start < end:
                raise ValueError('Invalid block extent')
            ops.append((cmd, start, end))
    expected = sum((end - start) * 4096 for cmd, start, end in ops if cmd == 'new')
    data = root / 'system.new.dat'
    if data.stat().st_size != expected:
        raise ValueError('Transfer list does not match decompressed data size')
    # Pinned full OTA: zero/erase ranges must not overlap new data.
    ordered = sorted((start, end) for _, start, end in ops)
    if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:])):
        raise ValueError('Overlapping extents require a different reconstruction algorithm')
    with data.open('rb') as src, (root / 'system.img').open('wb') as dst:
        dst.truncate(max(end for _, _, end in ops) * 4096)
        for cmd, start, end in ops:
            if cmd == 'new':
                dst.seek(start * 4096)
                remaining = (end - start) * 4096
                while remaining:
                    chunk = src.read(min(remaining, 1024 * 1024))
                    if not chunk:
                        raise ValueError('Truncated block data')
                    dst.write(chunk)
                    remaining -= len(chunk)

def inventory(root):
    entries = []
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            p = Path(current) / name
            entry = {'path': p.relative_to(root).as_posix()}
            if p.is_symlink():
                entry.update(type='symlink', target=os.readlink(p))
            elif p.is_file():
                entry.update(type='file', size=p.stat().st_size, sha256=digest(p))
            elif p.is_dir():
                entry.update(type='directory')
            else:
                entry.update(type='special')
            entries.append(entry)
    return sorted(entries, key=lambda e: e['path'])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--zip', type=Path, help='Use an already downloaded original V2 ZIP')
    args = parser.parse_args()
    out = args.output.resolve()
    if any(c.isspace() for c in str(out)):
        parser.error('Use an output path without whitespace (debugfs command syntax)')
    for executable in ('brotli', 'debugfs') + (() if args.zip else ('curl',)):
        if not shutil.which(executable):
            parser.error('Missing tool: ' + executable)
    out.mkdir(parents=True, exist_ok=False)
    archive = args.zip.resolve() if args.zip else out / 'original-v2.zip'
    if not args.zip:
        subprocess.run(['curl', '-fL', '--retry', '2', URL, '-o', str(archive)], check=True)
    if digest(archive) != SHA256:
        raise ValueError('Original release checksum mismatch; stop without extracting')
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            p = Path(info.filename)
            if p.is_absolute() or '..' in p.parts or ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError('Unsafe archive entry')
        z.extractall(out)
    subprocess.run(['brotli', '-d', str(out / 'system.new.dat.br'), '-o', str(out / 'system.new.dat')], check=True)
    reconstruct(out)
    tree = out / 'extracted'
    tree.mkdir()
    result = subprocess.run(['debugfs', '-R', 'rdump / ' + str(tree), str(out / 'system.img')], capture_output=True, text=True, check=True)
    (out / 'extraction.log').write_text(result.stdout + result.stderr)
    for line in (result.stdout + result.stderr).splitlines():
        if line and not line.startswith('debugfs ') and 'while changing ownership of ' not in line:
            raise RuntimeError('Unexpected debugfs output; inspect extraction.log: ' + line)
    # Legacy boot header used by this pinned ROM. Preserve original boot.img.
    boot = (out / 'boot.img').read_bytes()
    if boot[:8] != b'ANDROID!':
        raise ValueError('Unsupported boot image')
    ks, ka, rs, ra, ss, sa, ta, page, dt, unused = struct.unpack_from('<10I', boot, 8)
    if page not in (2048, 4096, 8192, 16384):
        raise ValueError('Unexpected boot page size')
    align = lambda n: (n + page - 1) // page * page
    bdir = out / 'boot-unpacked'
    bdir.mkdir()
    (bdir / 'kernel').write_bytes(boot[page:page + ks])
    rstart = page + align(ks)
    (bdir / 'ramdisk').write_bytes(boot[rstart:rstart + rs])
    dstart = rstart + align(rs) + align(ss)
    (bdir / 'dt.img').write_bytes(boot[dstart:dstart + dt])
    header = dict(kernel_size=ks, ramdisk_size=rs, second_size=ss, page_size=page, dt_size=dt,
                  cmdline=boot[64:576].split(b'\0')[0].decode(), sha256=digest(out / 'boot.img'))
    (bdir / 'header.json').write_text(json.dumps(header, indent=2) + '\n')
    manifest = dict(source=URL, archive_sha256=SHA256, system_sha256=digest(out / 'system.img'),
                    note='File-content inventory only; Android metadata remains in system.img.', files=inventory(tree))
    (out / 'inventory.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Extracted pinned V2:', tree)
    print('Retain system.img for original Android filesystem metadata.')

if __name__ == '__main__':
    main()
