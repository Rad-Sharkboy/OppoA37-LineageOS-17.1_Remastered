#!/usr/bin/env python3
"""Reproduce isolated E019 Android API29 zlib/libpng candidates (Linux/WSL)."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, tarfile, urllib.request

PINS = {
    'zlib-1.4': ('https://zlib.net/zlib-1.4.tar.gz', '02dd159783677a749c04adbdd02b55b8a2bcc7e054f51b76b549199a916ad584'),
    'libpng-1.6.59': ('https://downloads.sourceforge.net/project/libpng/libpng16/1.6.59/libpng-1.6.59.tar.gz', '86a3e4b501f7f50e392c4e456ea158893e9a595b1c63eb88c7bb9f6cf8772dad'),
}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--ndk',type=Path,required=True)
    p.add_argument('--cmake',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    here=Path(__file__).resolve().parent
    args.work.mkdir(parents=True,exist_ok=True)
    source=args.work/'src'; source.mkdir(exist_ok=True)
    for name,(url,sha) in PINS.items():
        archive=source/(name+'.tar.gz')
        if not archive.exists(): urllib.request.urlretrieve(url,archive)
        assert hashlib.sha256(archive.read_bytes()).hexdigest()==sha, name+' source mismatch'
        if not (source/name).exists():
            with tarfile.open(archive) as t: t.extractall(source,filter='data')
    for name in ['CMakeLists.txt','probe.c','aeabi.c']:
        if here/name != args.work/name: shutil.copy2(here/name,args.work/name)
    for abi,libdir in [('arm64-v8a','lib64'),('armeabi-v7a','lib')]:
        build=args.work/('build-'+abi)
        for stale in [build/'zlib/libz.so',build/'png/libpng.so']:
            if stale.is_symlink(): stale.unlink()
        command=[str(args.cmake),'-S',str(args.work),'-B',str(build),'-G','Ninja',
            '-DCMAKE_MAKE_PROGRAM='+str(args.cmake.parent/'ninja'),
            '-DCMAKE_TOOLCHAIN_FILE='+str(args.ndk/'build/cmake/android.toolchain.cmake'),
            '-DANDROID_ABI='+abi,'-DANDROID_PLATFORM=android-29','-DCMAKE_BUILD_TYPE=Release',
            '-DCMAKE_C_FLAGS_RELEASE=-O3 -DNDEBUG -ffunction-sections -fdata-sections',
            '-DCMAKE_SHARED_LINKER_FLAGS=-Wl,--gc-sections -Wl,-z,max-page-size=4096',
            '-DUPSTREAM='+str(source)]
        with (args.work/('config-'+abi+'.log')).open('w') as log:
            subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
        with (args.work/('build-'+abi+'.log')).open('w') as log:
            subprocess.run([str(args.cmake),'--build',str(build),'-j8'],stdout=log,stderr=subprocess.STDOUT,check=True)
        dest=args.output/'payload/system'/libdir; dest.mkdir(parents=True,exist_ok=True)
        strip=args.ndk/'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
        for origin in [build/'zlib/libz.so',build/'png/libpng.so']:
            target=dest/origin.name; shutil.copy2(origin,target)
            subprocess.run([str(strip),'--strip-unneeded',str(target)],check=True)
        dest=args.output/'probes'/abi; dest.mkdir(parents=True,exist_ok=True)
        shutil.copy2(build/'probe',dest/'probe')
    (args.output/'source-pins.json').write_text(json.dumps(PINS,indent=2)+'\n')

if __name__=='__main__': main()
