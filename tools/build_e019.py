#!/usr/bin/env python3
"""Combine the verified E019 boot test and pinned System files."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

from build_v21 import ROOT, run


def validate_path(path):
    if not re.fullmatch(r'system(?:/[A-Za-z0-9_.@+-]+)+', path):
        raise ValueError(f'Invalid System path: {path}')
    if any(component in ('.', '..') for component in path.split('/')):
        raise ValueError(f'Invalid System path: {path}')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def input_line(action, path, meta, old='-', new='-'):
    validate_path(path)
    if action == 'delete':
        return f'{action} {old} {new} {path} - - - -'
    return (f'{action} {old} {new} {path} {meta["uid"]} {meta["gid"]} '
            f'{meta["mode"]:o} {meta["selabel"]}')


def metadata_line(path, meta):
    return (f'set_metadata("/tmp/a37-e019-system/{path}", "uid", {meta["uid"]}, '
            f'"gid", {meta["gid"]}, "mode", 0{meta["mode"]:o}, '
            f'"capabilities", 0, "selabel", "{meta["selabel"]}");')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('kernel_package', 'payload', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()

    if run(['git', '-C', ROOT, 'status', '--porcelain']).stdout.strip():
        raise ValueError('Commit ROM sources first')
    head = run(['git', '-C', ROOT, 'rev-parse', 'HEAD']).stdout.strip()
    manifest = json.loads((args.kernel_package / 'build-manifest.json').read_text())
    if manifest['test'] != 'E019' or manifest['rom_commit'] != head:
        raise ValueError('Expected the current E019 boot test')

    sources = ROOT / 'tools/e019'
    profile = json.loads((sources / 'profile.json').read_text())
    edits, deletions, directories = (profile[key] for key in ('system_edits', 'deletions', 'directories'))
    if set(edits) & set(deletions) or set(directories) & (set(edits) | set(deletions)):
        raise ValueError('Conflicting System targets')

    with zipfile.ZipFile(args.kernel_package / 'E019-update.zip') as base:
        if base.testzip():
            raise ValueError('Boot ZIP readback failed')
        data = {name: base.read(name) for name in base.namelist()}
    boot_sha = manifest['boot']['sha256']
    if sha256(data['payload/boot.img']) != boot_sha or data['payload/boot.sha256'].decode().strip() != boot_sha:
        raise ValueError('Boot payload differs')
    if data['payload/base.sha256'].decode().strip() != manifest['base']['partition_sha256']:
        raise ValueError('Boot base differs')
    if data['payload/flash.sh'] != (ROOT / 'tools/kernel-test/flash.sh').read_bytes():
        raise ValueError('Boot helper differs')

    inputs = [input_line('directory', path, meta) for path, meta in directories.items()]
    for path, meta in edits.items():
        inputs.append(input_line('write', path, meta, meta.get('base_sha256', '-'), meta['sha256']))
        contents = (args.payload / path).read_bytes()
        if sha256(contents) != meta['sha256']:
            raise ValueError(f'System payload differs: {path}')
        data[f'system-files/{path}'] = contents
    for path, meta in deletions.items():
        inputs.append(input_line('delete', path, meta, meta['sha256']))
    data['scripts/inputs'] = ('\n'.join(inputs) + '\n').encode()

    helpers = ('prepare-system.sh', 'finish-system.sh')
    for name in helpers:
        data[f'scripts/{name}'] = (sources / name).read_bytes()
    lines = [
        'ui_print("Oppo A37 E019: volume placement, Trust cleanup, codecs and kernel.");',
        'package_extract_dir("payload", "/tmp/a37-kernel-test") || abort("Boot extraction failed.");',
        'set_metadata("/tmp/a37-kernel-test/flash.sh", "uid", 0, "gid", 0, "mode", 0755);',
        'run_program("/tmp/a37-kernel-test/flash.sh", "--check") == 0 || abort("Boot base differs.");',
        'package_extract_dir("scripts", "/tmp/a37-e019") || abort("Helper extraction failed.");',
    ]
    for name in helpers:
        lines.append(f'set_metadata("/tmp/a37-e019/{name}", "uid", 0, "gid", 0, "mode", 0755);')
    lines.extend([
        'run_program("/tmp/a37-e019/prepare-system.sh") == 0 || abort("System inputs differ.");',
        'package_extract_dir("system-files", "/tmp/a37-e019-system") || abort("System extraction failed.");',
    ])
    # Recovery returns an empty string from a successful set_metadata call.
    lines.extend(metadata_line(path, meta) for path, meta in directories.items())
    lines.extend(metadata_line(path, meta) for path, meta in edits.items())
    lines.extend([
        'run_program("/tmp/a37-e019/finish-system.sh") == 0 || abort("System readback failed.");',
        'run_program("/tmp/a37-kernel-test/flash.sh") == 0 || abort("Boot write failed.");',
        'ui_print("E019 installed. Reboot without wiping Data. First boot can take longer.");',
        '',
    ])
    data['META-INF/com/google/android/updater-script'] = '\n'.join(lines).encode()

    args.output.mkdir(parents=True, exist_ok=False)
    archive = args.output / 'E019-update.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for name, contents in data.items():
            output.writestr(name, contents)
    with zipfile.ZipFile(archive) as output:
        if output.testzip() or set(output.namelist()) != set(data):
            raise ValueError('ZIP readback failed')
        for name, contents in data.items():
            if output.read(name) != contents:
                raise ValueError(f'ZIP payload differs: {name}')

    manifest.update(profile, archive_bytes=archive.stat().st_size)
    (args.output / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Combined E019 built: {archive.stat().st_size} bytes')


if __name__ == '__main__':
    main()
