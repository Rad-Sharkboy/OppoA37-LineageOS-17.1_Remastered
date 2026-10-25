# V2 development baseline

The user confirmed this release matches the phone, including the CPU-idle property fix.

- Release: https://github.com/Rad-Sharkboy/OppoA37-LineageOS-17.1_Remastered/releases/tag/V2
- ZIP SHA-256: `446958b5e5ba36b23db6edc6f20caddfd5c0f01f0fb9ce26c294ffd82aa9ed9e`
- boot.img SHA-256: `46c4a31160e854a7178129872c602ba284840b5266fc56dc0c5c7ff0de7c7183`
- Embedded kernel: `3.10.108-Cinnamon-ExpA1-cinnamon-g6230b382fc7-dirty`, build #408, Linaro GCC 4.9.4.
- Kernel checkout at audit: `7fb4541df2a7eba5e246eec4aafb59eaf4d077ed`. It differs from the embedded kernel's named base commit, and the `dirty` changes are unknown. A successful build does not establish equivalence.
- Actual boot device tree has GPU active steps 200/310/620 MHz, plus 19.2 MHz level, and idle timeout 500 ms. Runtime caps, speed bin and active selection still require device readings.

## Reproduce extraction

Use Python 3, curl, brotli and debugfs (e2fsprogs), with at least 8 GB free. Run from this checkout:

```sh
python3 tools/unpack_v2.py /path/to/new-output-directory
# Or reuse your exact original ZIP:
python3 tools/unpack_v2.py /path/to/new-output-directory --zip /path/to/Lineage_17.1_REMASTERED_V2.zip
```

The script verifies the pinned download hash, validates transfer ranges and data size, reconstructs the ext4 image, extracts its files, splits the legacy boot image and writes a content inventory. It rejects a different release instead of silently importing it. No downloaded scripts or phone executables are executed.

In the prepared cloud machine, the extraction tools are local:

```sh
export PATH=/workspace/.onboarding/sysroot/usr/bin:/workspace/.onboarding/sysroot/usr/sbin:$PATH
export LD_LIBRARY_PATH=/workspace/.onboarding/sysroot/usr/lib/x86_64-linux-gnu
```

Do not source the kernel's Python 2 activation for Python 3 extraction.

`rom/v2/` contains 254 original editable UTF-8 files (properties, init rules, XML, shell scripts and related configuration). `rom/tracked-paths.json` lists their paths relative to the extracted filesystem root. `rom/v2-inventory.json` covers the whole extracted tree, including binaries and symlink targets. These files are the original baseline, with no performance edits.

Path example: `rom/v2/system/build.prop` maps to the kitchen's `system/system/build.prop` when the kitchen calls the image-root folder `system`, as in the user's screenshot.

Retain the original ZIP, boot.img and reconstructed system.img. Unprivileged extraction cannot restore every Android UID/GID, and the extracted tree does not reproduce all xattrs/capabilities. Expected ownership warnings are recorded. Git preserves neither Android ownership nor SELinux metadata; future repacks must use original image metadata or a kitchen that explicitly restores it. This repository is not a ready-to-flash rebuilt ROM.

## Evidence and priorities

1. **Runtime state first.** Boot cmdline sets `lpm_levels.sleep_disabled=1`, but `rom/v2/system/vendor/etc/init/hw/init.qcom.power.rc:51` resets it to 0 when `enable-low-power` runs. Read live state and `vendor.post_boot.parsed`; do not infer an idle-sleep bug from cmdline alone.
2. **GPU idle experiment.** V2's actual device tree sets 500 ms. Test 80 ms using E001 before considering a persistent edit; see BATTERY-TESTS.md.
3. **ROM/kernel governor conflict.** ROM requests `hispeed_freq=800000`, `go_hispeed_load=95`, `io_is_busy=0`. Kernel delayed work in `kernel/power/cinnamon_delay_trigger.c` requests 1209600, 75 and 1, and later changes target loads again. Capture after five minutes and after screen off/on. A later isolated experiment could stop that override or test a single governor parameter; do not delete the whole work function, which also touches I/O, VM and USB.
4. **Battery gauge limitations.** Current checkout's `drivers/power/oppo/oppo_bms.c` hardcodes -450 during discharge for projects 15109/15399 and estimates charge current. The embedded kernel's named base uses different constant current behavior; its dirty changes are unknown. Both require checking rather than treating apps' mA estimates as calibrated measurements. Current source substitutes a saved SOC before its later zero-SOC fallback; displayed percentage can be misleading. Gauge fixes must be a separate experiment from energy savings.
5. **IMS protection audit.** Current kernel delayed work adds `radio-interface`, `qcril` and `ims_socket_wake` to its userspace wakelock blocker. Exact-name blocking may interfere with suspend protection if these names occur. This does not prove a current call failure; read `/proc/wakelock_blocker` and test standby incoming calls/SMS/data. Do not expand the blocker.
6. **L2 power collapse.** Source disables the deeper L2 state with a documented wake-latency concern. Consider only after idle-state measurements; reenabling it may affect wake responsiveness.

Storage reduction and RAM savings are separate measurements. Preserve app caches when they reduce repeat CPU/I/O work; deleting them or forcing free RAM can increase energy use and relaunch latency. No debloat is applied before checking actual use and dependencies.
