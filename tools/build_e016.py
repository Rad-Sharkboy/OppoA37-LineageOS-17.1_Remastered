#!/usr/bin/env python3
"""Combine E016's verified boot and single-resource brightness overlay."""
import argparse,hashlib,json,zipfile
from pathlib import Path
from build_v21 import ROOT,digest,run

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('kernel_package','brightness','output'):p.add_argument(n,type=Path)
    a=p.parse_args()
    if run(['git','-C',ROOT,'status','--porcelain']).stdout.strip():
        raise ValueError('Commit source before packaging')
    head=run(['git','-C',ROOT,'rev-parse','HEAD']).stdout.strip()
    m=json.loads((a.kernel_package/'build-manifest.json').read_text())
    pins=json.loads((ROOT/'tools/brightness-overlay/inputs.json').read_text())
    binary=json.loads((ROOT/'tools/e016/profile.json').read_text())
    bm=json.loads((a.brightness/'brightness-manifest.json').read_text())
    apk=a.brightness/'A37Brightness.apk'
    if m['test']!='E016' or m['rom_commit']!=head:raise ValueError('Expected current E016 kernel package')
    if bm['framework_sha256']!=pins['framework_sha256'] or bm['framework_sha256']!=binary['framework_sha256'] or digest(apk)!=bm['apk_sha256'] or bm['apk_sha256']!=binary['apk_sha256']:
        raise ValueError('Brightness provenance differs')
    if bm['target_ms']!=8000 or bm['resource']!=pins['resource'] or bm['unchanged_ms']!=pins['unchanged_ms'] or bm['has_code']:
        raise ValueError('Brightness scope differs')
    with zipfile.ZipFile(a.kernel_package/'E016-update.zip') as z:
        if z.testzip():raise ValueError('Kernel ZIP differs')
        data={n:z.read(n) for n in z.namelist()}
    if hashlib.sha256(data['payload/boot.img']).hexdigest()!=m['boot']['sha256']:
        raise ValueError('Boot payload differs')
    if data['payload/flash.sh']!=(ROOT/'tools/kernel-test/flash.sh').read_bytes():
        raise ValueError('Boot installer differs')
    if data['payload/base.sha256'].decode().strip()!=m['base']['partition_sha256']:
        raise ValueError('Boot base differs')
    for name in ('prepare-system.sh','finish-system.sh'):
        data['scripts/'+name]=(ROOT/'tools/e016'/name).read_bytes()
    target='system/product/overlay/A37Brightness/A37Brightness.apk'
    data['system-files/'+target]=apk.read_bytes()
    data['scripts/inputs']=(pins['framework_sha256']+' '+pins['framework_sha256']+' system/framework/framework-res.apk\n').encode()
    data['scripts/overlay.sha256']=(bm['apk_sha256']+'\n').encode()
    lines=[
      'ui_print("Oppo A37 E016: RAM/compression, I/O, sensor fixes and 8-second dimming.");',
      'package_extract_dir("payload", "/tmp/a37-kernel-test") || abort("Cannot extract boot.");',
      'set_metadata("/tmp/a37-kernel-test/flash.sh", "uid", 0, "gid", 0, "mode", 0755);',
      'run_program("/tmp/a37-kernel-test/flash.sh", "--check") == 0 || abort("Boot base differs.");',
      'package_extract_dir("scripts", "/tmp/a37-e016") || abort("Cannot extract helpers.");']
    for name in ('prepare-system.sh','finish-system.sh'):
        lines.append(f'set_metadata("/tmp/a37-e016/{name}", "uid", 0, "gid", 0, "mode", 0755);')
    lines+=['run_program("/tmp/a37-e016/prepare-system.sh") == 0 || abort("System base checks failed.");',
      'package_extract_dir("system-files", "/tmp/a37-e016-system") || abort("Overlay install failed.");']
    directory=target.rsplit('/',1)[0]
    for path,mode in ((directory,'0755'),(target,'0644')):
        lines.append(f'set_metadata("/tmp/a37-e016-system/{path}", "uid", 0, "gid", 0, "mode", {mode}, "capabilities", 0, "selabel", "u:object_r:vendor_overlay_file:s0");')
    lines+=['run_program("/tmp/a37-e016/finish-system.sh") == 0 || abort("Overlay readback/finish failed.");',
      'run_program("/tmp/a37-kernel-test/flash.sh") == 0 || abort("Boot write failed.");',
      'ui_print("E016 installed; Magisk retained. Reboot without wiping Data.");','']
    data['META-INF/com/google/android/updater-script']='\n'.join(lines).encode()
    a.output.mkdir(parents=True,exist_ok=False)
    archive=a.output/'E016-update.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,content in data.items():z.writestr(name,content)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() or set(z.namelist())!=set(data):raise ValueError('ZIP readback failed')
        for name,content in data.items():
            if z.read(name)!=content:raise ValueError('ZIP payload differs: '+name)
    meta={'uid':0,'gid':0,'mode':0o644,'capabilities':0,'selabel':'u:object_r:vendor_overlay_file:s0','sha256':bm['apk_sha256']}
    m.update(system_edits={target:meta},brightness=bm,archive_bytes=archive.stat().st_size)
    (a.output/'build-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    (a.output/'boot.img').write_bytes(data['payload/boot.img'])
    print('Built',archive,'('+str(archive.stat().st_size)+' bytes)')

if __name__=='__main__':main()
