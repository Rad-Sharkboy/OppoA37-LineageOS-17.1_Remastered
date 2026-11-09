#!/usr/bin/env python3
import argparse,hashlib,json,re,subprocess,tempfile,zipfile
from pathlib import Path

def run(cmd):
    return subprocess.run([str(x) for x in cmd],check=True,capture_output=True,text=True).stdout
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    for n in ['framework','aapt2','keystore','password_file','output']:
        p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    a=p.parse_args();src=Path(__file__).resolve().parent
    pins=json.loads((src/'inputs.json').read_text())
    if digest(a.framework)!=pins['framework_sha256']:raise ValueError('Framework input differs')
    baseline=run([a.aapt2,'dump','resources',a.framework])
    for name,value in {pins['resource'].split('/')[-1]:pins['base_ms'],**pins['unchanged_ms']}.items():
        if not re.search(r'integer/'+name+r' PUBLIC\n\s+\(\) '+str(value)+r'\b',baseline):
            raise ValueError('Unexpected framework resource: '+name)
    a.output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='a37-overlay-') as temp:
        t=Path(temp)
        run([a.aapt2,'compile','--dir',src/'res','-o',t/'compiled.zip'])
        run([a.aapt2,'link','-I',a.framework,'--manifest',src/'AndroidManifest.xml',
             '--auto-add-overlay','-o',t/'unsigned.apk',t/'compiled.zip'])
        run(['jarsigner','-keystore',a.keystore,'-storepass:file',a.password_file,
             '-keypass:file',a.password_file,'-sigalg','SHA256withRSA','-digestalg','SHA-256',
             '-signedjar',t/'signed.apk',t/'unsigned.apk','a37_overlay'])
        apk=a.output/'A37Brightness.apk'
        run(['zipalign','-f','4',t/'signed.apk',apk])
    run(['zipalign','-c','4',apk])
    verify=run(['jarsigner','-verify',apk])
    if 'jar verified.' not in verify:raise ValueError('APK signature verification failed')
    resources=run([a.aapt2,'dump','resources',apk])
    if len(re.findall(r'^\s+resource 0x',resources,re.M))!=1:raise ValueError('Overlay has extra resources')
    if not re.search(r'integer/config_autoBrightnessDarkeningLightDebounce\b[^\n]*\n\s+\(\) 8000\b',resources):
        raise ValueError('Overlay value differs')
    manifest=run([a.aapt2,'dump','xmltree',apk,'--file','AndroidManifest.xml'])
    if 'org.a37.overlay.brightness' not in manifest or 'android:hasCode' not in manifest:
        raise ValueError('Overlay manifest differs')
    with zipfile.ZipFile(apk) as z:
        assert not z.testzip() and not any(n.endswith('.dex') for n in z.namelist())
    component=a.output/'brightness-8s-component.zip'
    files={'module.prop':(src/'module.prop').read_bytes(),'customize.sh':(src/'customize.sh').read_bytes(),
           'system/product/overlay/A37Brightness/A37Brightness.apk':apk.read_bytes()}
    with zipfile.ZipFile(component,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    with zipfile.ZipFile(component) as z:
        assert not z.testzip() and set(z.namelist())==set(files)
    result={'framework_sha256':pins['framework_sha256'],'apk_sha256':digest(apk),
            'resource':pins['resource'],'target_ms':8000,'unchanged_ms':pins['unchanged_ms'],
            'has_code':False,'phone_verification':'pending combined E016 reboot'}
    (a.output/'brightness-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Built brightness component: 8000ms; one resource; signature/alignment verified')

if __name__=='__main__':main()
