Build the pinned Android API 29 candidates with the NDK r28c Linux toolchain.

`python3 build.py --work /path/to/work --ndk /path/to/ndk --cmake /path/to/cmake --output /path/to/artifacts`

The output includes both ABIs for comparison. E019 selects only the ARM64 pair and ships the two upstream licenses from the pinned source archives. Keep the original Android SONAMEs and ELF exports required by the ROM.
