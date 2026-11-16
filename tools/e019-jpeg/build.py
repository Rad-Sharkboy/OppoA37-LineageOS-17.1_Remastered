#!/usr/bin/env python3
"""Rebuild E019's Android 10 libjpeg pair from the pinned official source."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

VERSION = "3.2.1"
SOURCE_URL = "https://github.com/libjpeg-turbo/libjpeg-turbo/releases/download/3.2.1/libjpeg-turbo-3.2.1.tar.gz"
SOURCE_SHA256 = "c27ad72a68da151177929aa969ae773a2da5ac2af9ce946079314fdac8cece7f"
TAG_COMMIT = "7b4993786d856cbccabfc0ed2f923ba000e326cc"
BASE_HASHES = {
    "system/lib/libjpeg.so": "593d1fd6cbace55a52154c7bc25cc88cc0e1c6177e28631d139aa0e3c3429ca4",
    "system/lib64/libjpeg.so": "2d5b8e87a92f7d1e89df2ca81e7958a19dc81a18e7697999ca3a6fdf56f112ae",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, log):
    with log.open("w") as stream:
        subprocess.run([str(arg) for arg in args], stdout=stream,
                       stderr=subprocess.STDOUT, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ndk", type=Path, required=True)
    ap.add_argument("--cmake-bin", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)
    props = (args.ndk / "source.properties").read_text()
    if "Pkg.Revision = 28.2.13676358" not in props:
        raise SystemExit("Recipe pins Android NDK r28c (28.2.13676358)")
    archive = args.work / f"libjpeg-turbo-{VERSION}.tar.gz"
    if not archive.exists():
        urllib.request.urlretrieve(SOURCE_URL, archive)
    if sha256(archive) != SOURCE_SHA256:
        raise SystemExit("Official source SHA-256 mismatch")
    source = args.work / f"libjpeg-turbo-{VERSION}"
    # Refuse source reuse, so a locally modified tree cannot enter the payload.
    if source.exists():
        raise SystemExit(f"Choose a fresh --work; source already exists: {source}")
    with tarfile.open(archive) as tf:
        for item in tf.getmembers():
            dest = (args.work / item.name).resolve()
            if not dest.is_relative_to(args.work.resolve()):
                raise SystemExit("Unsafe archive path")
        tf.extractall(args.work)
    build_config = source / "sharedlib/CMakeLists.txt"
    text = build_config.read_text()
    if text.count("if(MAPFLAG)\n") != 1:
        raise SystemExit("Pinned source configuration changed")
    # AOSP exports are unversioned and include jsimd entry points. The NDK's
    # Android CMake platform already emits SONAME libjpeg.so without an ABI suffix.
    build_config.write_text("# E019 Android compatibility: preserve unversioned exports.\n" + text.replace("if(MAPFLAG)\n",
                                         "if(MAPFLAG AND NOT ANDROID)\n", 1))
    errors = source / "src/jerror.c"
    error_source = errors.read_text()
    old = "static const char * const jpeg_std_message_table[] = {"
    if error_source.count(old) != 1:
        raise SystemExit("Pinned message table declaration changed")
    errors.write_text(error_source.replace(old,
        "/* E019 Android compatibility: retain the original diagnostic export. */\n"
        "const char * const jpeg_std_message_table[] = {", 1))
    profile = {
        "component": "libjpeg-turbo", "version": VERSION,
        "source_url": SOURCE_URL, "source_sha256": SOURCE_SHA256,
        "tag_commit": TAG_COMMIT, "release_date": "2026-10-27",
        "android_api": 29, "ndk": "28.2.13676358", "jpeg_lib_version": 62,
        "simd": "NEON", "export_policy": "unversioned, like original Android build",
        "files": [],
    }
    for abi, folder in [("armeabi-v7a", "lib"), ("arm64-v8a", "lib64")]:
        build = args.work / abi
        configure = [args.cmake_bin / "cmake", "-S", source, "-B", build,
                     "-G", "Ninja",
                     f"-DCMAKE_MAKE_PROGRAM={args.cmake_bin / 'ninja'}",
                     f"-DCMAKE_TOOLCHAIN_FILE={args.ndk / 'build/cmake/android.toolchain.cmake'}",
                     f"-DANDROID_ABI={abi}", "-DANDROID_PLATFORM=android-29",
                     "-DANDROID_ARM_NEON=TRUE", "-DANDROID_STL=none",
                     "-DENABLE_SHARED=ON", "-DENABLE_STATIC=OFF",
                     "-DWITH_TURBOJPEG=OFF", "-DWITH_TOOLS=OFF",
                     "-DWITH_TESTS=OFF", "-DWITH_JPEG7=OFF", "-DWITH_JPEG8=OFF",
                     "-DWITH_SIMD=ON", "-DBUILD=20261027",
                     "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_C_FLAGS_RELEASE=-O3 -DNDEBUG"]
        run(configure, args.work / f"configure-{abi}.log")
        run([args.cmake_bin / "cmake", "--build", build, "-j", "8"],
            args.work / f"build-{abi}.log")
        dest = args.out / "payload/system" / folder / "libjpeg.so"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(build / "libjpeg.so", dest)
        run([args.ndk / "toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip",
             "--strip-unneeded", dest], args.work / f"strip-{abi}.log")
        profile["files"].append({"path": f"system/{folder}/libjpeg.so",
                                 "sha256": sha256(dest), "size": dest.stat().st_size})
    notice = args.out / "payload/system/etc/NOTICE.E019-libjpeg-turbo.txt"
    notice.parent.mkdir(parents=True, exist_ok=True)
    notice.write_text("libjpeg-turbo 3.2.1 (E019 Android compatibility build)\n"
        "This software is based in part on the work of the Independent JPEG Group.\n\n"
        + (source / "LICENSE.md").read_text() + "\n\n"
        + (source / "README.ijg").read_text())
    profile["files"].append({"path": "system/etc/NOTICE.E019-libjpeg-turbo.txt",
                             "sha256": sha256(notice), "size": notice.stat().st_size})
    profile["system_edits"] = {}
    for item in profile["files"]:
        path = item["path"]
        profile["system_edits"][path] = {
            "base_sha256": BASE_HASHES.get(path, "-"),
            "sha256": item["sha256"], "uid": 0, "gid": 0, "mode": 0o644,
            "selabel": "u:object_r:system_lib_file:s0" if path.endswith(".so")
                       else "u:object_r:system_file:s0",
        }
    (args.out / "profile.json").write_text(json.dumps(profile, indent=2) + "\n")


if __name__ == "__main__":
    main()
