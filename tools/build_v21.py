#!/usr/bin/env python3
"""Build the pinned V2.1 full OTA from V2 metadata and the reviewed kernel.

Requires debugfs/e2fsck/dumpe2fs, brotli and Python 3. Output must be new.
No Android owner, mode or extended attribute is inferred from extracted files.
"""
import argparse, ctypes, hashlib, json, mmap, os, re, shutil, struct, subprocess, zipfile
from pathlib import Path

V2_ZIP_SHA = '446958b5e5ba36b23db6edc6f20caddfd5c0f01f0fb9ce26c294ffd82aa9ed9e'
V2_SYSTEM_SHA = 'd2b619ab1dc679ba745f2d77918d0eb996f9b90d1e8f90e1276810b9ea98d20e'
KERNEL_SHA = '2e97c93cd24a83c352ad3e777d98a5eebe0dbe2fad823d8ee77f9ea20d0e3160'
HAL_SHA = '018006128be9745a77dbbb37b44408c69e94dee42b418a088da23bc42a82c1de'
ROOT = Path(__file__).resolve().parents[1]
BLOCK = 4096

def digest(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def run(argv, ok=(0,)):
    r = subprocess.run([str(x) for x in argv], text=True, capture_output=True)
    if r.returncode not in ok: raise RuntimeError(f'{argv[0]} failed ({r.returncode}): {r.stdout}{r.stderr}')
    return r

def debug(image, command, write=False):
    r = run(['debugfs', *(['-w'] if write else []), '-R', command, image])
    if any(x in r.stderr for x in ['File not found', 'Could not', 'Usage:', 'while ', 'already exists']):
        raise RuntimeError(command + ': ' + r.stderr)
    return r.stdout

def metadata(image, path, cache):
    s = debug(image, 'stat ' + path)
    head = re.search(r'Inode: (\d+)\s+Type: regular\s+Mode:\s+([0-7]+)\s+Flags: (0x[0-9a-f]+)', s)
    if not head: raise ValueError('Not a regular file: ' + path)
    owner = re.search(r'User:\s+(\d+)\s+Group:\s+(\d+)\s+Size:\s+(\d+)', s)
    if not re.search(r'Links: 1\s', s): raise ValueError('Unexpected hardlinks: ' + path)
    result = dict(inode=int(head[1]), mode=int(head[2], 8), flags=head[3], uid=int(owner[1]), gid=int(owner[2]), size=int(owner[3]), xattrs={})
    result['generation'] = int(re.search(r'Generation: (\d+)', s)[1])
    result['extra_isize'] = int(re.search(r'Size of extra inode fields: (\d+)', s)[1])
    result['times'] = {m[1]: [int(m[2], 16), int(m[3], 16)] for m in re.finditer(r'^\s*(ctime|atime|mtime|crtime): (0x[0-9a-f]+):([0-9a-f]+)', s, re.M)}
    for name in re.findall(r'^  ([\w.]+) \(\d+\) =', s, re.M):
        dest = cache / (hashlib.sha256(path.encode()).hexdigest()[:12] + '-' + name)
        debug(image, f'ea_get -f {dest} {path} {name}')
        result['xattrs'][name] = dest.read_bytes().hex()
    return result

def replace_file(image, path, source, meta, cache, exists=True):
    if exists: debug(image, 'rm ' + path, True)
    result = debug(image, f'write {source} {path}', True)
    if 'Allocated inode:' not in result: raise RuntimeError(result)
    fields = {'mode': f'0{0o100000 | meta["mode"]:o}', 'uid': meta['uid'], 'gid': meta['gid'],
              'flags': meta['flags'], 'generation': meta['generation'], 'extra_isize': meta['extra_isize']}
    for key, value in fields.items(): debug(image, f'sif {path} {key} {value}', True)
    for key, value in meta['xattrs'].items():
        data = cache / ('restore-' + key); data.write_bytes(bytes.fromhex(value))
        debug(image, f'ea_set -f {data} {path} {key}', True)
    for key, value in meta['times'].items():
        debug(image, f'sif {path} {key} @{value[0]}', True)
        debug(image, f'sif {path} {key}_extra {value[1]}', True)
    actual = metadata(image, path, cache)
    for key in ['mode', 'flags', 'uid', 'gid', 'generation', 'extra_isize', 'times', 'xattrs']:
        if actual[key] != meta[key]: raise ValueError(f'Metadata changed: {path} {key}: {actual[key]} != {meta[key]}')
    dump = cache / 'readback'; debug(image, f'dump {path} {dump}')
    if digest(dump) != digest(source): raise ValueError('File readback mismatch: ' + path)
    return actual

def boot_image(original, kernel, dest):
    old = original.read_bytes(); k = kernel.read_bytes()
    if old[:8] != b'ANDROID!' or k[56:60] != b'ARM\x64': raise ValueError('Boot/kernel format mismatch')
    ks, ka, rs, ra, ss, sa, ta, page, dt, os_version = struct.unpack_from('<10I', old, 8)
    if page != 2048 or ss: raise ValueError('Unexpected legacy boot layout')
    align = lambda n: (n + page - 1) // page * page
    rstart = page + align(ks); dstart = rstart + align(rs) + align(ss)
    if dstart + align(dt) != len(old): raise ValueError('Unexpected boot footer')
    ramdisk = old[rstart:rstart + rs]; device_tree = old[dstart:dstart + dt]
    def image_id(raw_kernel):
        h = hashlib.sha1()
        for data in [raw_kernel, ramdisk, b'', device_tree]: h.update(data); h.update(struct.pack('<I', len(data)))
        return h.digest()
    if old[576:596] != image_id(old[page:page + ks]): raise ValueError('Original boot ID mismatch')
    header = bytearray(old[:page]); struct.pack_into('<I', header, 8, len(k)); header[576:608] = image_id(k) + bytes(12)
    padded = lambda b: b + bytes(align(len(b)) - len(b))
    dest.write_bytes(header + padded(k) + padded(ramdisk) + padded(device_tree))
    new = dest.read_bytes(); unchanged = bytearray(new[:page]); unchanged[8:12] = old[8:12]; unchanged[576:608] = old[576:608]
    assert unchanged == old[:page]
    assert new[page + align(len(k)):page + align(len(k)) + rs] == ramdisk
    assert new[page + align(len(k)) + align(rs):page + align(len(k)) + align(rs) + dt] == device_tree
    return dict(bytes=len(new), sha256=digest(dest), ramdisk_sha256=hashlib.sha256(ramdisk).hexdigest(), dt_sha256=hashlib.sha256(device_tree).hexdigest())

def free_ranges(image, output):
    text = run(['dumpe2fs', image]).stdout; (output / 'filesystem.txt').write_text(text)
    count = int(re.search(r'^Block count:\s+(\d+)', text, re.M)[1])
    assert int(re.search(r'^Block size:\s+(\d+)', text, re.M)[1]) == BLOCK
    free_count = int(re.search(r'^Free blocks:\s+(\d+)', text, re.M)[1]); ranges = []
    for line in re.findall(r'^  Free blocks: (.*)$', text, re.M):
        for item in line.split(','):
            item = item.strip()
            if not item: continue
            parts = [int(v) for v in item.split('-')]; a = parts[0]; b = parts[-1] + 1
            ranges.append((a, b))
    assert sum(b-a for a,b in ranges) == free_count
    assert all(0 <= a < b <= count for a,b in ranges)
    assert all(a[1] <= b[0] for a,b in zip(ranges, ranges[1:]))
    return count, ranges

def transfer(image, output):
    count, free = free_ranges(image, output); assert image.stat().st_size == count * BLOCK
    flags = bytearray(count)
    libc = ctypes.CDLL(None, use_errno=True); libc.fallocate.argtypes = [ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_longlong]
    with image.open('r+b') as f:
        for a,b in free:
            flags[a:b] = bytes([1]) * (b-a)
            if libc.fallocate(f.fileno(), 3, a*BLOCK, (b-a)*BLOCK): raise OSError(ctypes.get_errno(), 'Cannot normalize free blocks')
    runs = {'new': [], 'zero': [], 'erase': free}; zero = bytes(BLOCK)
    with image.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm, (output/'system.new.dat').open('wb') as data:
        for i in range(count):
            if flags[i]: continue
            chunk = mm[i*BLOCK:(i+1)*BLOCK]; kind = 'zero' if chunk == zero else 'new'
            if runs[kind] and runs[kind][-1][1] == i: runs[kind][-1][1] += 1
            else: runs[kind].append([i,i+1])
            if kind == 'new': data.write(chunk)
    lines = ['4', str(count-sum(b-a for a,b in free)), '0', '0']
    for kind in ['erase', 'new', 'zero']:
        pending=[]; blocks=0
        def emit():
            if pending: lines.append(kind+' '+','.join(map(str,[len(pending)*2]+[n for pair in pending for n in pair])))
        for a,b in runs[kind]:
            while a < b:
                room = 512-blocks if kind == 'new' else b-a
                end = min(b,a+room); pending.append([a,end]); blocks += end-a; a=end
                if len(pending) == 128 or (kind == 'new' and blocks == 512): emit();pending=[];blocks=0
        emit()
    (output/'system.transfer.list').write_text('\n'.join(lines)+'\n');(output/'system.patch.dat').write_bytes(b'')
    # Reconstruct from the emitted commands, including explicit zero/erase ranges.
    rebuilt=output/'roundtrip-system.img'
    with rebuilt.open('wb') as dst, (output/'system.new.dat').open('rb') as src:
        dst.truncate(count*BLOCK); seen=bytearray(count)
        for line in lines[4:]:
            kind, encoded=line.split();v=list(map(int,encoded.split(',')));assert v[0]==len(v)-1
            for a,b in zip(v[1::2],v[2::2]):
                assert not any(seen[a:b]);seen[a:b]=bytes([1])*(b-a)
                if kind == 'new':
                    size=(b-a)*BLOCK;chunk=src.read(size);assert len(chunk)==size;dst.seek(a*BLOCK);dst.write(chunk)
        assert all(seen) and src.read(1)==b''
    assert digest(rebuilt)==digest(image)
    rebuilt.unlink()
    return dict(blocks=count, new_bytes=(output/'system.new.dat').stat().st_size, transfer_commands=len(lines)-4)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('baseline',type=Path);ap.add_argument('original_zip',type=Path);ap.add_argument('kernel',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--quality',type=int,default=9,choices=range(0,12));args=ap.parse_args()
    for p in [args.baseline,args.original_zip,args.kernel,args.output,ROOT]:
        if any(c.isspace() for c in str(p)): raise ValueError('Use paths without whitespace')
    for tool in ['debugfs','e2fsck','dumpe2fs','brotli']: assert shutil.which(tool),tool
    if digest(args.original_zip)!=V2_ZIP_SHA or digest(args.baseline/'system.img')!=V2_SYSTEM_SHA or digest(args.kernel)!=KERNEL_SHA: raise ValueError('Pinned input hash mismatch')
    with zipfile.ZipFile(args.original_zip) as original:
        for name in ['boot.img','META-INF/com/google/android/update-binary']:
            if original.read(name)!=(args.baseline/name).read_bytes(): raise ValueError('Original ZIP component differs: '+name)
    args.output.mkdir(parents=True,exist_ok=False);out=args.output;cache=out/'metadata-cache';cache.mkdir()
    print('Preparing original ext4 metadata and boot components...',flush=True)
    image=out/'system.img';run(['cp','--sparse=always',args.baseline/'system.img',image])
    edits={}
    targets=['system/build.prop','system/vendor/etc/init/hw/init.qcom.power.rc','system/vendor/etc/init/android.hardware.power@1.2-service-qti.rc','system/vendor/bin/a37-power-profile.sh']
    hal='system/vendor/bin/hw/android.hardware.power@1.2-service-qti';patched=out/'power-hal'
    run(['sh','-c','. "$1"; a37_patch_hal "$2" "$3"','patch',ROOT/'tools/power-profile-bridge/payload.sh',args.baseline/'extracted'/hal,patched]);assert digest(patched)==HAL_SHA
    for name in targets+[hal]:
        exists=name!='system/vendor/bin/a37-power-profile.sh'
        template='/'+name if exists else '/system/vendor/bin/init.qcom.mem.sh'
        meta=metadata(args.baseline/'system.img',template,cache)
        source=patched if name==hal else ROOT/'rom/v2'/name
        actual=replace_file(image,'/'+name,source,meta,cache,exists)
        edits[name]={'sha256':digest(source),'bytes':source.stat().st_size,'metadata':actual}
    fixed=run(['e2fsck','-fy',image],ok=(0,1));(out/'fsck-repair.txt').write_text(fixed.stdout+fixed.stderr)
    checked=run(['e2fsck','-fn',image]);(out/'fsck-check.txt').write_text(checked.stdout+checked.stderr)
    boot=boot_image(args.baseline/'boot.img',args.kernel,out/'boot.img');(out/'boot.sha256').write_text(boot['sha256']+'\n')
    print('Generating and verifying full OTA block ranges...',flush=True)
    blocks=transfer(image,out)
    run(['e2fsck','-fn',image])
    manifest={'release':'V2.1','rom_commit':run(['git','-C',ROOT,'rev-parse','HEAD']).stdout.strip(),'source_zip_sha256':V2_ZIP_SHA,'kernel_sha256':KERNEL_SHA,'boot':boot,'system_sha256':digest(image),'edits':edits,'transfer':blocks,'brotli_quality':args.quality}
    (out/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Compressing Android block payload...',flush=True)
    run(['brotli','-q',str(args.quality),'-w','24',out/'system.new.dat','-o',out/'system.new.dat.br'])
    run(['brotli','-t',out/'system.new.dat.br'])
    decoded=hashlib.sha256()
    with subprocess.Popen(['brotli','-d','-c',str(out/'system.new.dat.br')],stdout=subprocess.PIPE) as proc:
        for chunk in iter(lambda:proc.stdout.read(1024*1024),b''):decoded.update(chunk)
        if proc.wait():raise RuntimeError('Brotli readback failed')
    assert decoded.hexdigest()==digest(out/'system.new.dat')
    manifest['system_dat_sha256']=decoded.hexdigest()
    print('Creating flashable V2.1 ZIP...',flush=True)
    archive=out/'Lineage_17.1_REMASTERED_V2.1.zip'
    files={name:out/name for name in ['boot.img','boot.sha256','system.new.dat.br','system.transfer.list','system.patch.dat']}
    files['META-INF/com/google/android/update-binary']=args.baseline/'META-INF/com/google/android/update-binary'
    files['META-INF/com/google/android/updater-script']=ROOT/'tools/v21/updater-script'
    for name in ['prepare.sh','flash_kernel.sh','cleanup-tuning.sh']:files['META-INF/scripts/'+name]=ROOT/'tools/v21'/name
    with zipfile.ZipFile(archive,'w',allowZip64=True) as z:
        for name,path in files.items():
            info=zipfile.ZipInfo(name,(2026,10,28,0,0,0));info.create_system=3;info.external_attr=0o100644<<16
            info.compress_type=zipfile.ZIP_STORED if name.endswith('.br') else zipfile.ZIP_DEFLATED
            with z.open(info,'w',force_zip64=False) as dst,path.open('rb') as src:shutil.copyfileobj(src,dst,1024*1024)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,path in files.items():
            h=hashlib.sha256()
            with z.open(name) as f:
                for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
            assert h.hexdigest()==digest(path),name
    checksum=digest(archive);(out/'SHA256SUMS').write_text(checksum+'  '+archive.name+'\n')
    manifest.update(zip_bytes=archive.stat().st_size,zip_sha256=checksum,system_brotli_bytes=(out/'system.new.dat.br').stat().st_size)
    (out/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'zip':str(archive),'bytes':archive.stat().st_size,'sha256':checksum},indent=2),flush=True)

if __name__=='__main__':main()
