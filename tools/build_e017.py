#!/usr/bin/env python3
"""Add the selected disabled-logd retry fix to a verified E017 boot test."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
from build_v21 import ROOT,digest,run

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('kernel_package',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 if run(['git','-C',ROOT,'status','--porcelain']).stdout.strip():raise ValueError('Commit source first')
 head=run(['git','-C',ROOT,'rev-parse','HEAD']).stdout.strip()
 m=json.loads((a.kernel_package/'build-manifest.json').read_text())
 if m['test']!='E017' or m['rom_commit']!=head:raise ValueError('Expected current E017 boot package')
 pins=json.loads((ROOT/'tools/e017/profile.json').read_text())['targets']
 if set(pins)!={'system/etc/init/logd.rc'}:raise ValueError('Unexpected System edit')
 with zipfile.ZipFile(a.kernel_package/'E017-update.zip') as z:
  if z.testzip():raise ValueError('Boot ZIP differs')
  data={n:z.read(n) for n in z.namelist()}
 if hashlib.sha256(data['payload/boot.img']).hexdigest()!=m['boot']['sha256']:raise ValueError('Boot differs')
 if data['payload/base.sha256'].decode().strip()!=m['base']['partition_sha256']:raise ValueError('Boot base differs')
 if data['payload/flash.sh']!=(ROOT/'tools/kernel-test/flash.sh').read_bytes():raise ValueError('Boot installer differs')
 for name in ('prepare-system.sh','finish-system.sh'):
  data['scripts/'+name]=(ROOT/'tools/e017'/name).read_bytes()
 edits={};checks=[]
 for name,meta in pins.items():
  source=ROOT/'rom/v2'/name
  if digest(source)!=meta['sha256']:raise ValueError('System source differs')
  if not source.read_bytes().startswith(b'service logd /system/bin/logd\n    oneshot\n    disabled\n'):raise ValueError('Logger policy differs')
  data['system-files/'+name]=source.read_bytes();edits[name]=meta
  checks.append(meta['base_sha256']+' '+meta['sha256']+' '+name)
 data['scripts/inputs']=('\n'.join(checks)+'\n').encode()
 lines=['ui_print("Oppo A37 E017: power cleanup and quieter logging; retaining Magisk.");',
  'package_extract_dir("payload", "/tmp/a37-kernel-test") || abort("Cannot extract boot.");',
  'set_metadata("/tmp/a37-kernel-test/flash.sh", "uid", 0, "gid", 0, "mode", 0755);',
  'run_program("/tmp/a37-kernel-test/flash.sh", "--check") == 0 || abort("Boot base differs.");',
  'package_extract_dir("scripts", "/tmp/a37-e017") || abort("Cannot extract helpers.");']
 for name in ('prepare-system.sh','finish-system.sh'):
  lines.append(f'set_metadata("/tmp/a37-e017/{name}", "uid", 0, "gid", 0, "mode", 0755);')
 lines+=['run_program("/tmp/a37-e017/prepare-system.sh") == 0 || abort("System base checks failed.");',
  'package_extract_dir("system-files", "/tmp/a37-e017-system") || abort("System update failed.");']
 for name,meta in edits.items():
  lines.append(f'set_metadata("/tmp/a37-e017-system/{name}", "uid", {meta["uid"]}, "gid", {meta["gid"]}, "mode", 0{meta["mode"]:o}, "capabilities", 0, "selabel", "{meta["selabel"]}");')
 lines+=['run_program("/tmp/a37-e017/finish-system.sh") == 0 || abort("System readback/finish failed.");',
  'run_program("/tmp/a37-kernel-test/flash.sh") == 0 || abort("Boot write failed.");',
  'ui_print("E017 installed. Reboot without wiping Data.");','']
 updater='\n'.join(lines)
 if re.search(r'set_metadata\([^\n]*\)\s*\|\|',updater):raise ValueError('Invalid empty-success check')
 data['META-INF/com/google/android/updater-script']=updater.encode()
 a.output.mkdir(parents=True,exist_ok=False)
 archive=a.output/'E017-update.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for name,content in data.items():z.writestr(name,content)
 with zipfile.ZipFile(archive) as z:
  if z.testzip() or set(z.namelist())!=set(data):raise ValueError('ZIP readback failed')
  for name,content in data.items():
   if z.read(name)!=content:raise ValueError('Payload differs: '+name)
 m.update(system_edits=edits,archive_bytes=archive.stat().st_size)
 (a.output/'build-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 (a.output/'boot.img').write_bytes(data['payload/boot.img'])
 print('Built',archive,'('+str(archive.stat().st_size)+' bytes)')

if __name__=='__main__':main()
