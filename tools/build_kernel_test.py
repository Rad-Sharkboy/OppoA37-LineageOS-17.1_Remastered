#!/usr/bin/env python3
"""Pack a local A37 kernel test against an explicitly verified installed boot."""
import argparse, hashlib, json, re, struct, zipfile
from pathlib import Path
from build_v21 import boot_image, digest, run, ROOT

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tag',required=True)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--base-inputs',type=Path,required=True)
    p.add_argument('--kernel',type=Path,required=True)
    p.add_argument('--kernel-sha',required=True)
    p.add_argument('--kernel-source',type=Path,required=True)
    p.add_argument('--kernel-commit',required=True)
    p.add_argument('--update-binary',type=Path,required=True)
    p.add_argument('--update-binary-sha',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if not re.fullmatch(r'E[0-9]{3}',a.tag):raise ValueError('Invalid test tag')
    for root in [ROOT,a.kernel_source]:
        if run(['git','-C',root,'status','--porcelain']).stdout.strip():raise ValueError('Commit source before packaging')
    if run(['git','-C',a.kernel_source,'rev-parse','HEAD']).stdout.strip()!=a.kernel_commit:raise ValueError('Unexpected kernel source head')
    if digest(a.kernel)!=a.kernel_sha:raise ValueError('Unexpected raw Image')
    if digest(a.update_binary)!=a.update_binary_sha:raise ValueError('Unexpected installer binary')
    kernel=a.kernel.read_bytes()
    banner=re.search(rb'Linux version ([^ \x00]+) ',kernel)
    if not banner or not banner[1].endswith((a.tag+'-g'+a.kernel_commit[:8]).encode()):raise ValueError('Kernel version does not match clean source')
    inputs=json.loads(a.base_inputs.read_text())
    if digest(a.base)!=inputs['partition_sha256']:raise ValueError('Installed boot capture differs')
    base=a.base.read_bytes()
    if base[:8]!=b'ANDROID!':raise ValueError('Expected legacy Android boot')
    ks,ka,rs,ra,ss,sa,ta,page,dt,osv=struct.unpack_from('<10I',base,8)
    if page!=2048 or ss or not dt:raise ValueError('Unexpected A37 layout')
    align=lambda n:(n+page-1)//page*page
    end=page+align(ks)+align(rs)+align(dt)
    if end>len(base) or any(base[end:]):raise ValueError('Review boot footer')
    ramdisk=base[page+align(ks):page+align(ks)+rs]
    tree=base[page+align(ks)+align(rs):page+align(ks)+align(rs)+dt]
    for data,key in [(base[page:page+ks],'kernel_sha256'),(ramdisk,'ramdisk_sha256'),(tree,'dt_sha256')]:
        if hashlib.sha256(data).hexdigest()!=inputs[key]:raise ValueError('Base component differs: '+key)
    a.output.mkdir(parents=True,exist_ok=False)
    original=a.output/'installed-boot.img';original.write_bytes(base[:end])
    image=a.output/'boot.img'
    result=boot_image(original,a.kernel,image)
    if result['ramdisk_sha256']!=inputs['ramdisk_sha256'] or result['dt_sha256']!=inputs['dt_sha256']:raise ValueError('Boot components changed')
    (a.output/'boot.sha256').write_text(result['sha256']+'\n')
    (a.output/'base.sha256').write_text(inputs['partition_sha256']+'\n')
    script=ROOT/'tools/kernel-test/flash.sh'
    updater='\n'.join([
      f'ui_print("Oppo A37 {a.tag} kernel test; retaining installed Magisk.");',
      'package_extract_dir("payload", "/tmp/a37-kernel-test") || abort("Cannot extract kernel test.");',
      'set_metadata("/tmp/a37-kernel-test/flash.sh", "uid", 0, "gid", 0, "mode", 0755);',
      'run_program("/tmp/a37-kernel-test/flash.sh") == 0 || abort("Kernel test checks/write failed.");',
      'ui_print("Installed. Reboot without wiping Data.");',''])
    files={'META-INF/com/google/android/update-binary':a.update_binary,
           'payload/boot.img':image,'payload/boot.sha256':a.output/'boot.sha256',
           'payload/base.sha256':a.output/'base.sha256','payload/flash.sh':script}
    archive=a.output/(a.tag+'-update.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('META-INF/com/google/android/updater-script',updater)
        for name,path in files.items():z.write(path,name)
    with zipfile.ZipFile(archive) as z:
        if z.testzip():raise ValueError('Archive readback failed')
        for name,path in files.items():
            if z.read(name)!=path.read_bytes():raise ValueError('Archive payload differs')
    manifest={'test':a.tag,'kernel_commit':a.kernel_commit,'kernel_sha256':a.kernel_sha,
              'rom_commit':run(['git','-C',ROOT,'rev-parse','HEAD']).stdout.strip(),
              'base':inputs,'boot':result,'archive_bytes':archive.stat().st_size}
    (a.output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Built',archive,'('+str(archive.stat().st_size)+' bytes)')

if __name__=='__main__':main()
