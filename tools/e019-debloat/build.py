#!/usr/bin/env python3
"""Exact-input Trust removal; preserve Android credentials and keyguard callbacks."""
import argparse,hashlib,json,re,struct,subprocess,tempfile,zipfile,zlib
from pathlib import Path
import xml.etree.ElementTree as ET

def run(cmd):return subprocess.run([str(x) for x in cmd],check=True,capture_output=True,text=True).stdout
def sha(data):return hashlib.sha256(data).hexdigest()
def digest(p):return sha(p.read_bytes())
def uleb(data,pos):
 value=shift=0
 while True:
  byte=data[pos];pos+=1;value|=(byte&127)<<shift
  if not byte&128:return value,pos
  shift+=7
  if shift>35:raise ValueError('Malformed uleb128')
def method_code(d,clazz,name,signature):
 def table(pos):return struct.unpack_from('<2I',d,pos)
 ns,so=table(56);nt,to=table(64);np,po=table(72);nm,mo=table(88);nc,co=table(96)
 strings=[]
 for i in range(ns):
  p=struct.unpack_from('<I',d,so+i*4)[0];_,p=uleb(d,p);strings.append(d[p:d.index(0,p)].decode('utf8','replace'))
 types=[strings[struct.unpack_from('<I',d,to+i*4)[0]] for i in range(nt)]
 prototypes=[]
 for i in range(np):
  _,ret,p=struct.unpack_from('<3I',d,po+i*12);args=[]
  if p:
   n=struct.unpack_from('<I',d,p)[0];args=[types[struct.unpack_from('<H',d,p+4+j*2)[0]] for j in range(n)]
  prototypes.append('('+''.join(args)+')'+types[ret])
 targets=[]
 for i in range(nm):
  c,p,n=struct.unpack_from('<HHI',d,mo+i*8)
  if types[c]==clazz and strings[n]==name and prototypes[p]==signature:targets.append(i)
 assert len(targets)==1
 for i in range(nc):
  c,_,_,_,_,_,p,_=struct.unpack_from('<8I',d,co+i*32)
  if types[c]!=clazz:continue
  counts=[]
  for _ in range(4):v,p=uleb(d,p);counts.append(v)
  for _ in range(counts[0]+counts[1]):_,p=uleb(d,p);_,p=uleb(d,p)
  for n in counts[2:]:
   index=0
   for _ in range(n):
    delta,p=uleb(d,p);index+=delta;_,p=uleb(d,p);code,p=uleb(d,p)
    if index==targets[0]:return code
 raise ValueError('Method code not found')
def patch_services(original,pins):
 assert sha(original)==pins['system/framework/services.jar']['sha256']
 with zipfile.ZipFile(__import__('io').BytesIO(original)) as z:
  assert not any(n.upper().endswith(('.RSA','.DSA','.EC','.SF')) for n in z.namelist())
  data=bytearray(z.read('classes.dex'));before=bytes(data)
  off=method_code(data,'Lcom/android/server/policy/keyguard/KeyguardStateMonitor;','onShowingStateChanged','(ZI)V')
  assert off==0x52de60
  assert struct.unpack_from('<4H',data,off)==(5,3,3,2)
  assert struct.unpack_from('<I',data,off+12)[0]==54
  patch=off+16+12*2;assert data[patch:patch+4]==bytes.fromhex('54240f60')
  data[patch:patch+4]=bytes.fromhex('0e000000')
  data[12:32]=hashlib.sha1(data[32:]).digest();struct.pack_into('<I',data,8,zlib.adler32(data[12:])&0xffffffff)
  assert data[off:patch]==before[off:patch] and data[patch+4:]==before[patch+4:]
  assert all(i in range(8,32) or i in range(patch,patch+4) for i,(a,b) in enumerate(zip(before,data)) if a!=b)
  return z.namelist(),[(info,bytes(data) if info.filename=='classes.dex' else z.read(info.filename)) for info in z.infolist()],bytes(data)
def main():
 p=argparse.ArgumentParser()
 for n in ('image','framework','platform','aapt2','keystore','password_file','output'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
 a=p.parse_args();src=Path(__file__).resolve().parent;pins=json.loads((src/'inputs.json').read_text())
 assert digest(a.framework)==pins['system/framework/framework-res.apk']['sha256']
 assert digest(a.platform)==pins['system/framework/org.lineageos.platform-res.apk']['sha256']
 a.output.mkdir(parents=True,exist_ok=True);payload=a.output/'payload';payload.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='a37-trust-') as tmp:
  t=Path(tmp)
  def extract(path):
   out=t/Path(path).name;run(['debugfs','-R','dump /'+path+' '+str(out),a.image]);assert digest(out)==pins[path]['sha256'];return out
  original=extract('system/framework/services.jar')
  names,entries,dex=patch_services(original.read_bytes(),pins);(t/'classes.dex').write_bytes(dex)
  run(['/mnt/c/Users/faiza/AppData/Local/Android/Sdk/build-tools/35.0.0/dexdump','-c',t/'classes.dex'])
  jar=payload/'system/framework/services.jar';jar.parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(t/'services.jar','w') as z:
   for info,data in entries:z.writestr(info,data)
  run(['zipalign','-f','4',t/'services.jar',jar]);run(['zipalign','-c','4',jar])
  with zipfile.ZipFile(jar) as z:
   assert z.namelist()==names and not z.testzip()
   for info,data in entries:assert z.read(info.filename)==data
  manifest=extract('system/vendor/etc/vintf/manifest.xml').read_bytes()
  pattern=rb'    <hal format="hidl">\n        <name>vendor\.lineage\.trust</name>\n.*?    </hal>\n'
  modified,n=re.subn(pattern,b'',manifest,flags=re.S);assert n==1
  old=ET.fromstring(manifest);new=ET.fromstring(modified);oldh=[e for e in old if e.tag=='hal'];newh=[e for e in new if e.tag=='hal'];assert len(oldh)==len(newh)+1
  assert [ET.tostring(e) for e in oldh if e.findtext('name')!='vendor.lineage.trust']==[ET.tostring(e) for e in newh]
  mp=payload/'system/vendor/etc/vintf/manifest.xml';mp.parent.mkdir(parents=True,exist_ok=True);mp.write_bytes(modified)
  base=run([a.aapt2,'dump','resources',a.platform]);m=re.search(r'array/config_externalLineageServices\n\s+\(\) \(array\) size=7\n(.*?)(?=\n\s+resource )',base,re.S);assert m
  old_services=re.findall(r'"([^"]+)"',m[1]);desired=[e.text for e in ET.parse(src/'res/values/config.xml').getroot().find('string-array')]
  assert old_services==desired[:5]+['org.lineageos.platform.internal.TrustInterfaceService']+desired[5:]
  run([a.aapt2,'compile','--dir',src/'res','-o',t/'compiled.zip'])
  run([a.aapt2,'link','-I',a.framework,'-I',a.platform,'--manifest',src/'AndroidManifest.xml','--auto-add-overlay','-o',t/'unsigned.apk',t/'compiled.zip'])
  run(['jarsigner','-keystore',a.keystore,'-storepass:file',a.password_file,'-keypass:file',a.password_file,'-sigalg','SHA256withRSA','-digestalg','SHA-256','-signedjar',t/'signed.apk',t/'unsigned.apk','a37_overlay'])
  overlay=payload/'system/product/overlay/A37TrustCleanup/A37TrustCleanup.apk';overlay.parent.mkdir(parents=True,exist_ok=True);run(['zipalign','-f','4',t/'signed.apk',overlay])
  assert 'jar verified.' in run(['jarsigner','-verify',overlay]);resources=run([a.aapt2,'dump','resources',overlay]);assert len(re.findall(r'^\s+resource 0x',resources,re.M))==1 and 'size=6' in resources and 'TrustInterfaceService' not in resources
  assert re.findall(r'"(org\.lineageos\.platform\.internal\.[^"]+)"',resources)==desired
  with zipfile.ZipFile(overlay) as z:assert not z.testzip() and not any(n.endswith('.dex') for n in z.namelist())
  deletions={path:meta for path,meta in pins.items() if meta.get('delete')}
  for path in deletions:extract(path)
  edits={str(jar.relative_to(payload)):{'base_sha256':pins['system/framework/services.jar']['sha256'],'sha256':digest(jar),'uid':0,'gid':0,'mode':420,'selabel':'u:object_r:system_file:s0'},str(mp.relative_to(payload)):{'base_sha256':pins['system/vendor/etc/vintf/manifest.xml']['sha256'],'sha256':digest(mp),'uid':0,'gid':0,'mode':420,'selabel':'u:object_r:vendor_configs_file:s0'},str(overlay.relative_to(payload)):{'sha256':digest(overlay),'uid':0,'gid':0,'mode':420,'selabel':'u:object_r:system_file:s0'}}
  result={'system_edits':edits,'deletions':deletions,'disable_components':['org.lineageos.lineageparts/.trust.TrustOnBoardingActivity','org.lineageos.lineageparts/.trust.TrustPreferences'],'precondition':{'/proc/sys/kernel/deny_new_usb':'0'},'changes':{'keyguard':'return after unchanged state/callback prefix; keep tail/try ranges','services_preopt':'invalidate only services artifacts; ART settings unchanged','shared_framework_classes':'retained inert to preserve SDK ABI/signatures'},'validation':'exact inputs; DEX prefix/tail/SHA1/Adler; dexdump checksum; single-resource signed static RRO; VINTF removes only Trust HAL'}
  (a.output/'profile.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Built Trust cleanup: keyguard hook, service-list overlay, HAL + feature removal; provenance verified.')
if __name__=='__main__':main()
