# A37 V2 native Power HAL profile bridge

User installation, quick comparison and rollback: [POWER-PROFILES.md](../../docs/POWER-PROFILES.md).

This directory contains original extension source, a deterministic patch builder, a generated text payload and Magisk installation helpers. It does not contain the original proprietary HAL or a flashable ROM. The installer patches a copy on the phone and verifies the entire output before staging the overlay.

## Pinned input and build

Input: `/vendor/bin/hw/android.hardware.power@1.2-service-qti` from the original V2 system image, little-endian AArch64 ELF64 PIE, 29,808 bytes.

```text
Original SHA-256:
0acfe2bafdcffea00b492f9cd21932b5cf606bc49e0a29e69c64c401a555db15
Published patched SHA-256:
018006128be9745a77dbbb37b44408c69e94dee42b418a088da23bc42a82c1de
```

Rebuild outside the repository, using Python 3, Debian `aarch64-linux-gnu-gcc` 14.2.0-19 and matching binutils (2.44):

```sh
python3 tools/power-profile-bridge/build.py \
  /path/to/extracted/system/vendor/bin/hw/android.hardware.power@1.2-service-qti \
  /path/to/output --cross-prefix /usr/bin/aarch64-linux-gnu-
```

The output includes the patched HAL, `metadata.json`, the extension ELF/raw code and `payload.sh`. Compare the generated payload with this directory's published payload. Different compiler versions can produce different code and hashes; always validate a rebuilt payload as a new patch. The builder refuses an unexpected original hash, ABI, program-header layout or function prologue. It rejects unresolved symbols, GOT/data/BSS additions and code larger than one 4 KiB page.

## Native event route

Lineage's `PerformanceManagerService` sends `POWER_HINT_SET_PROFILE=0x111` to PowerManager. Profile IDs are Power Save=0, Balanced=1 and Performance=2 for this HAL's supported three-profile configuration. The saved preference lives in `content://lineagesettings/secure`, key `performance_profile`; an ordinary Android `settings get secure` query is not authoritative. Battery Saver and application profiles can make the active profile differ from the user's saved preference.

The patch hooks the exact binary's `power_hint_override` at `0x4840` and `set_interactive_override` at `0x4b70`. Each trampoline reproduces the displaced stack allocation and executes the original body before applying the extension. Other hints keep their original behavior. Profile and screen callbacks are serialized by this service's one-thread HIDL RPC pool. No additional thread, service or periodic wake-up is added to the HAL.

The extension uses position-independent AArch64 code and raw `openat/read/write/close` syscalls for existing sysfs controls. It never opens with `O_CREAT`. The existing `dlsym` PLT entry resolves `__system_property_set` for two new diagnostic properties: `vendor.a37.profile` and `vendor.a37.profile_apply`. These record the active received hint and whether the writes succeeded, rather than guessing a profile from clocks or a screenshot. Successful writes are not proof of instantaneous operating frequency; status reads back the controls.

## ELF layout and permissions

The 1,819-byte extension is placed at file offset / virtual address `0x8000`. A redundant `PT_NOTE` descriptor becomes a page-aligned read/execute `PT_LOAD`; the original notes, Android API note and section table remain in place. The GNU build ID is updated to identify the modified image. The 16-byte state at `0x70c0` extends the original writable segment within its existing final BSS page, outside GNU RELRO. No writable/executable segment is introduced. The output grows by 4,779 bytes including alignment padding, to 34,587 bytes.

The original service runs as `system:system`. Existing init/ueventd rules grant its CPU governor, CPU minimum and GPU idle controls. The module adds only `system:system`, mode `0664`, to GPU `devfreq/min_freq`, retaining read access. It copies the original HAL's SELinux file context to the overlay. It does not change SELinux mode or policy.

The native path applies E001/E002/E003 to Balanced/Power Save and higher frequency floors plus the original boost/table/delay in Performance. It writes no maximum-frequency, thermal, sleep-disable, input-boost, idler-workload, display or radio control. The one-time Magisk late-start reconciliation waits 300 seconds for old V2 kernel writers, reads the active HAL marker, applies the same policy and exits. It does not infer an active profile from the saved preference. A recognized old E002 helper is backed up and removed to avoid a competing unconditional writer.

## Thermal and policy interaction

This V2 thermal-engine uses KGSL `max_gpuclk`; the kernel turns that into `thermal_pwrlevel`, which dominates requested GPU levels. CPU thermal limits also clamp the minimum when reducing the maximum. Existing caps exposed through the read CPU/devfreq maximum nodes are respected before setting floors. The independent performance daemon can impose further limits asynchronously; device readback is still needed.

Linux 3.10 devfreq refuses a new `max_freq` below its current `min_freq`. While Performance holds the devfreq floor high, another tuning tool cannot lower that particular maximum without first lowering the floor. Select Balanced before applying such external GPU limits. This is distinct from V2's thermal-engine route, which remains effective. The reported GPU devfreq minimum is a requested floor; KGSL thermal throttling can run the GPU below it.

## Validation record

Local ARM64 emulation executed the generated branch hooks, trampolines and compiled policy at two different ASLR bases. It covered profiles 2→1→0, unrelated/invalid hints, screen events, CPU0 offline with CPU2 available, lower exposed maximums, denied writes and diagnostic properties. Original return values, stack and callee-saved registers were preserved; file descriptors were closed. The emulated original function bodies and Android services were stubs.

Local shell fixtures covered 35 invocations across E005 and this module: exact patch byte/hash equality, install guards, failed-stage cleanup, previous-helper backup/removal/restoration, profile values, missing CPU, delayed-start cancellation and a profile switch during boot reconciliation. Root, Magisk and ownership/SELinux operations were stubbed. Real Android ELF loading, Magisk mounts, Binder/perfd interaction and physical-device behavior require the documented phone check. Harnesses remain local outside the kernel repository.

Source references:

- [Lineage 17.1 performance service](https://github.com/LineageOS/android_lineage-sdk/blob/lineage-17.1/lineage/lib/main/java/org/lineageos/platform/internal/PerformanceManagerService.java)
- [Lineage profile constants](https://github.com/LineageOS/android_lineage-sdk/blob/lineage-17.1/sdk/src/java/lineageos/power/PerformanceManager.java)
- [Lineage settings provider contract](https://github.com/LineageOS/android_lineage-sdk/blob/lineage-17.1/sdk/src/java/lineageos/providers/LineageSettings.java)
- [Magisk module layout and boot scripts](https://topjohnwu.github.io/Magisk/guides.html)
- Device kernel: `drivers/gpu/msm/kgsl_pwrctrl.c`, `drivers/devfreq/devfreq.c`, `drivers/cpufreq/cpufreq.c`, `drivers/thermal/msm_thermal.c` and `drivers/soc/qcom/msm_performance.c`.
