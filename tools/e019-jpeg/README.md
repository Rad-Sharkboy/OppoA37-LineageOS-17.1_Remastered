# E019 Android JPEG build

Builds libjpeg-turbo 3.2.1 for Android API 29, ARMv7 NEON and ARM64 NEON, using
Android NDK r28c (28.2.13676358) and CMake/Ninja. The official release tarball,
SHA-256 and tag commit are pinned in `build.py`. Source and generated binaries
stay outside Git. No change to camera libraries or ART settings is included.

```sh
python3 tools/e019-jpeg/build.py \
  --ndk /path/to/android-ndk-r28c \
  --cmake-bin /path/to/cmake/bin \
  --work /path/to/fresh-work-directory \
  --out /path/to/output
```

The output contains `payload/system/lib/libjpeg.so`, the ARM64 counterpart,
a required upstream notice, and `profile.json` with hashes and original Android
metadata. The shared-library ABI remains JPEG v6b (62), with unversioned Android
exports and `libjpeg.so` SONAME. Two small source adaptations disable Unix symbol
versioning and retain Android's old `jpeg_std_message_table` diagnostic export.
TurboJPEG and command-line tools are disabled; upstream's newer 12/16-bit core
entry points remain because the supported build has no option to remove them.

Use the generated original-hash checks for installation. Roll back both library
files together to the pinned V2 originals. These source files do not install on
the phone, and building does not establish full camera or app compatibility.
