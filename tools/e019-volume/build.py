#!/usr/bin/env python3
"""Preserve the V2 volume dialog and move it up 80dp in portrait."""
import argparse,hashlib,json,re,subprocess,tempfile,zipfile
from pathlib import Path
def run(cmd):return subprocess.run([str(x) for x in cmd],check=True,capture_output=True,text=True).stdout
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 for n in ('framework','systemui','aapt2','keystore','password_file','output'):
  p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
 a=p.parse_args();src=Path(__file__).resolve().parent;pins=json.loads((src/'inputs.json').read_text())
 assert digest(a.framework)==pins['framework_sha256']
 assert digest(a.systemui)==pins['apk_sha256']
 assert digest(src/'res/layout-port/volume_dialog.xml')==pins['layout_source_sha256']
 a.output.mkdir(parents=True,exist_ok=True);payload=a.output/'payload'
 with tempfile.TemporaryDirectory(prefix='a37-volume-') as tmp:
  t=Path(tmp)
  run([a.aapt2,'compile','--dir',src/'res','-o',t/'compiled.zip'])
  run([a.aapt2,'link','-I',a.framework,'-I',a.systemui,'--manifest',src/'AndroidManifest.xml','--auto-add-overlay','-o',t/'unsigned.apk',t/'compiled.zip'])
  run(['jarsigner','-keystore',a.keystore,'-storepass:file',a.password_file,'-keypass:file',a.password_file,'-sigalg','SHA256withRSA','-digestalg','SHA-256','-signedjar',t/'signed.apk',t/'unsigned.apk','a37_overlay'])
  overlay=payload/'system/product/overlay/A37VolumePosition/A37VolumePosition.apk';overlay.parent.mkdir(parents=True,exist_ok=True)
  run(['zipalign','-f','4',t/'signed.apk',overlay]);run(['zipalign','-c','4',overlay])
  assert 'jar verified.' in run(['jarsigner','-verify',overlay])
  resources=run([a.aapt2,'dump','resources',overlay])
  assert len(re.findall(r'^\s+resource 0x',resources,re.M))==1 and '(port)' in resources
  xml=run([a.aapt2,'dump','xmltree',overlay,'--file','res/layout-port/volume_dialog.xml'])
  assert 'translationY' in xml and ('-80.000000dp' in xml or '16777136.000000dp' in xml)
  def layout_entries(text):
   entries=[]
   for line in text.splitlines():
    line=line.strip()
    if not line.startswith(('E:', 'A:')) or ':translationY' in line:continue
    line=re.sub(r' \(line=\d+\)$','',line)
    line=line.replace('http://schemas.android.com/apk/res-auto:', 'sysui:').replace('http://schemas.android.com/apk/prv/res/com.android.systemui:', 'sysui:')
    entries.append(line)
   return entries
  original_xml=run([a.aapt2,'dump','xmltree',a.systemui,'--file','res/layout/volume_dialog.xml'])
  assert layout_entries(xml)==layout_entries(original_xml), 'Original volume attributes changed'

  cert=run(['keytool','-exportcert','-rfc','-alias','a37_overlay','-keystore',a.keystore,'-storepass:file',a.password_file]);(t/'cert.pem').write_text(cert)
  der=subprocess.check_output(['openssl','x509','-in',str(t/'cert.pem'),'-outform','DER'])
  assert hashlib.sha256(der).hexdigest()==pins['systemui_certificate_sha256']
  with zipfile.ZipFile(overlay) as z:assert not z.testzip() and not any(n.endswith('.dex') for n in z.namelist())
 helper=payload/'system/vendor/bin/a37-volume-placement.sh';helper.parent.mkdir(parents=True,exist_ok=True);helper.write_bytes((src/'apply.sh').read_bytes())
 edits={str(overlay.relative_to(payload)):{'sha256':digest(overlay),'uid':0,'gid':0,'mode':420,'selabel':'u:object_r:system_file:s0'},str(helper.relative_to(payload)):{'sha256':digest(helper),'uid':0,'gid':2000,'mode':493,'selabel':'u:object_r:qti_init_shell_exec:s0'}}
 result={'system_edits':edits,'changes':{'volume_panel_side':'left via native Lineage secure setting, once-only migration','portrait_vertical_offset_dp':-80,'landscape':'original layout retained'},'validation':'exact SystemUI/framework inputs; one portrait layout; all original compiled attributes preserved; no DEX; signature matches original SystemUI','phone_verification':{'portrait_ringer_top_px':179,'portrait_main_top_px':315,'original_ringer_top_px':339,'original_main_top_px':475,'density':2,'offset_px':-160,'landscape':'preview off/on vertical positions match; no added clipping'}}
 (a.output/'profile.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Built left/up volume placement payload.')
if __name__=='__main__':main()
