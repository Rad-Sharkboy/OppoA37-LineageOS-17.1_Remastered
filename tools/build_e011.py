#!/usr/bin/env python3
"""Add the E011 profile files to a verified E011 kernel test."""
import argparse, hashlib, json, zipfile
from pathlib import Path
from build_v21 import ROOT, digest, run

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('kernel_package',type=Path)
    p.add_argument('hal',type=Path)
    p.add_argument('hal_metadata',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    if run(['git','-C',ROOT,'status','--porcelain']).stdout.strip():
        raise ValueError('Commit source before packaging')
    head=run(['git','-C',ROOT,'rev-parse','HEAD']).stdout.strip()
    m=json.loads((a.kernel_package/'build-manifest.json').read_text())
    pins=json.loads((ROOT/'tools/e011/profile.json').read_text())
    hm=json.loads(a.hal_metadata.read_text())
    if m['test']!='E011' or m['rom_commit']!=head or m['boot']['dt_patch']['profile']!='a37-cpu-plan-e011':
        raise ValueError('Expected the current E011 kernel package')
    if digest(a.hal)!=pins['hal_sha256'] or hm['patched_sha256']!=pins['hal_sha256'] or hm['original_sha256']!=pins['original_hal_sha256']:
        raise ValueError('E011 HAL provenance differs')
    targets=pins['targets']
    expected={'system/vendor/bin/hw/android.hardware.power@1.2-service-qti',
              'system/vendor/bin/a37-power-profile.sh','system/vendor/etc/init/hw/init.qcom.power.rc'}
    if set(targets)!=expected:raise ValueError('Unexpected System targets')
    with zipfile.ZipFile(a.kernel_package/'E011-update.zip') as z:
        data={name:z.read(name) for name in z.namelist()}
    if hashlib.sha256(data['payload/boot.img']).hexdigest()!=m['boot']['sha256']:
        raise ValueError('Kernel payload differs')
    if data['payload/base.sha256'].decode().strip()!=m['base']['partition_sha256']:
        raise ValueError('Installed boot pin differs')
    if data['payload/flash.sh']!=(ROOT/'tools/kernel-test/flash.sh').read_bytes():
        raise ValueError('Kernel installer differs')
    data['scripts/prepare-system.sh']=(ROOT/'tools/e011/prepare-system.sh').read_bytes()
    data['scripts/finish-system.sh']=(ROOT/'tools/e011/finish-system.sh').read_bytes()
    lines=['ui_print("Oppo A37 E011: CPU targets + 800 MHz profiles; retaining Magisk.");',
      'package_extract_dir("payload", "/tmp/a37-kernel-test") || abort("Cannot extract boot.");',
      'set_metadata("/tmp/a37-kernel-test/flash.sh", "uid", 0, "gid", 0, "mode", 0755);',
      'run_program("/tmp/a37-kernel-test/flash.sh", "--check") == 0 || abort("Boot base differs.");',
      'package_extract_dir("scripts", "/tmp/a37-e011") || abort("Cannot extract helpers.");']
    for name in ['prepare-system.sh','finish-system.sh']:
        lines.append(f'set_metadata("/tmp/a37-e011/{name}", "uid", 0, "gid", 0, "mode", 0755);')
    lines.append('run_program("/tmp/a37-e011/prepare-system.sh") == 0 || abort("System base checks failed.");')
    checks=[];edits={}
    for name,meta in targets.items():
        source=a.hal if name.endswith('/android.hardware.power@1.2-service-qti') else ROOT/'rom/v2'/name
        content=source.read_bytes();sha=hashlib.sha256(content).hexdigest()
        data['system-profile/'+name]=content
        checks.append(meta['base_sha256']+' '+sha+' '+name)
        edits[name]={**meta,'sha256':sha}
    data['scripts/inputs']=('\n'.join(checks)+'\n').encode()
    lines.append('package_extract_dir("system-profile", "/tmp/a37-e011-system") || abort("Profile install failed.");')
    for name,meta in targets.items():
        lines.append(f'set_metadata("/tmp/a37-e011-system/{name}", "uid", {meta["uid"]}, "gid", {meta["gid"]}, "mode", 0{meta["mode"]:o}, "capabilities", 0, "selabel", "{meta["selabel"]}");')
    lines+=['run_program("/tmp/a37-e011/finish-system.sh") == 0 || abort("System finish failed.");',
      'run_program("/tmp/a37-kernel-test/flash.sh") == 0 || abort("Boot write failed.");',
      'ui_print("E011 installed. Reboot; no Data wipe needed.");','']
    data['META-INF/com/google/android/updater-script']='\n'.join(lines).encode()
    a.output.mkdir(parents=True,exist_ok=False)
    archive=a.output/'E011-update.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,content in data.items():z.writestr(name,content)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() or set(z.namelist())!=set(data):raise ValueError('ZIP readback failed')
        for name,content in data.items():
            if z.read(name)!=content:raise ValueError('ZIP payload differs: '+name)
    m.update(system_edits=edits,archive_bytes=archive.stat().st_size)
    (a.output/'build-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    (a.output/'boot.img').write_bytes(data['payload/boot.img'])
    print('Built',archive,'('+str(archive.stat().st_size)+' bytes)')

if __name__=='__main__':main()
