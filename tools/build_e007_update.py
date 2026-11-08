#!/usr/bin/env python3
"""Build the small combined E007 TWRP update for the installed V2.1 base."""
import argparse, json, shutil, zipfile
from pathlib import Path
from build_v21 import digest, run, ROOT

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('verified_full_build',type=Path)
    p.add_argument('original_v2',type=Path)
    p.add_argument('hal',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    m=json.loads((a.verified_full_build/'build-manifest.json').read_text())
    if m['release']!='V2.1 E007' or digest(a.verified_full_build/'boot.img')!=m['boot']['sha256']:
        raise ValueError('Expected the verified E007 boot component')
    if digest(a.hal)!=m['hal_sha256']:
        raise ValueError('Expected the validated E007 native HAL')
    if run(['git','-C',ROOT,'status','--porcelain']).stdout.strip():
        raise ValueError('Commit source before packaging')
    a.output.mkdir(parents=True,exist_ok=False)
    scripts=ROOT/'tools/e007'
    files={
      'boot.img':a.verified_full_build/'boot.img',
      'boot.sha256':a.verified_full_build/'boot.sha256',
      'META-INF/com/google/android/update-binary':a.original_v2/'META-INF/com/google/android/update-binary',
    }
    for n in ['prepare.sh','flash_kernel.sh','cleanup-tuning.sh','mount_update.sh','finish_update.sh']:
        files['META-INF/scripts/'+n]=scripts/n
    targets=list(m['edits'])
    expected={'system/build.prop','system/vendor/etc/init/hw/init.qcom.power.rc','system/vendor/etc/init/android.hardware.power@1.2-service-qti.rc','system/vendor/bin/a37-power-profile.sh','system/vendor/bin/hw/android.hardware.power@1.2-service-qti'}
    if set(targets)!=expected:raise ValueError('Unexpected update target list')
    lines=['ui_print("Oppo A37 E007 combined update over V2.1");',
           'package_extract_dir("META-INF/scripts", "/tmp") || abort("Cannot extract scripts.");',
           'package_extract_file("boot.img", "/tmp/boot.img") || abort("Cannot extract boot.");',
           'package_extract_file("boot.sha256", "/tmp/boot.sha256") || abort("Cannot extract boot verification.");']
    for n in ['prepare.sh','flash_kernel.sh','cleanup-tuning.sh','mount_update.sh','finish_update.sh']:
        lines.append(f'set_metadata("/tmp/{n}", "uid", 0, "gid", 0, "mode", 0755);')
    lines+=['run_program("/tmp/mount_update.sh") == 0 || abort("E007 base checks failed.");',
            'package_extract_dir("payload", "/tmp/a37-e007-system") || abort("Cannot install E007 files.");']
    edits={}
    for name in targets:
        source=a.hal if name.endswith('/android.hardware.power@1.2-service-qti') else ROOT/'rom/v2'/name
        files['payload/'+name]=source
        meta=m['edits'][name]['metadata']
        if set(meta['xattrs'])!={'security.selinux'}:raise ValueError('Review extended attributes: '+name)
        label=bytes.fromhex(meta['xattrs']['security.selinux']).rstrip(b'\0').decode()
        lines.append(f'set_metadata("/tmp/a37-e007-system/{name}", "uid", {meta["uid"]}, "gid", {meta["gid"]}, "mode", 0{meta["mode"]:o}, "capabilities", 0, "selabel", "{label}");')
        edits[name]={'sha256':digest(source),'uid':meta['uid'],'gid':meta['gid'],'mode':oct(meta['mode']),'selabel':label}
    lines+=['run_program("/tmp/finish_update.sh") == 0 || abort("Cannot finish System writes.");',
            'run_program("/tmp/flash_kernel.sh") == 0 || abort("Boot write failed.");',
            'ui_print("E007 installed. Reboot; no Data wipe is needed.");']
    updater=a.output/'updater-script';updater.write_text('\n'.join(lines)+'\n')
    files['META-INF/com/google/android/updater-script']=updater
    archive=a.output/'E007-update.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,path in files.items():z.write(path,name)
    with zipfile.ZipFile(archive) as z:
        if z.testzip():raise ValueError('ZIP readback failed')
        if set(z.namelist())!=set(files):raise ValueError('Unexpected package entries')
        for name,path in files.items():
            if z.read(name)!=path.read_bytes():raise ValueError('Package readback differs: '+name)
    (a.output/'build-manifest.json').write_text(json.dumps({'test':'E007 update','base':'V2.1','rom_commit':run(['git','-C',ROOT,'rev-parse','HEAD']).stdout.strip(),'kernel_commit':m['kernel_commit'],'boot':m['boot'],'edits':edits},indent=2)+'\n')
    print('Built local E007 update:',archive,'('+str(archive.stat().st_size)+' bytes)')

if __name__=='__main__':main()
