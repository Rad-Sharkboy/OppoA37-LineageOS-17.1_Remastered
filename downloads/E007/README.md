# E007 full test ROM — Oppo A37/A37f/A37fw

[Download the full E007 ROM](https://github.com/Rad-Sharkboy/OppoA37-LineageOS-17.1_Remastered/raw/refs/heads/e007-download/downloads/E007/Lineage_17.1_REMASTERED_V2.1_E007.zip) · [Original V2.1](https://github.com/Rad-Sharkboy/OppoA37-LineageOS-17.1_Remastered/tree/v2.1-download/downloads/V2.1)

This is a full ROM ZIP based on V2 with the retained V2.1 tuning and combined E007 changes. The working V2.1 download remains available. Use the direct ZIP link above; GitHub source-code archives can contain only LFS pointers.

## Install in TWRP

1. Download `Lineage_17.1_REMASTERED_V2.1_E007.zip` to the phone/SD card. Keep your working V2.1 ZIP available.
2. In TWRP, flash E007 over V2.1/V2. **Do not wipe or format Data.** System and Boot are replaced; installed apps/data are retained. Use normal custom-ROM installation with ZIP signature verification off.
3. Reboot and wait five minutes after Android finishes booting. The helper reconciles delayed kernel startup once, then exits. Reinstall Magisk afterward if you want root; this boot uses the original unpatched ramdisk.

Windows checksum:

```powershell
Get-FileHash .\Lineage_17.1_REMASTERED_V2.1_E007.zip -Algorithm SHA256
```

Expected SHA256: `5e68861799878e38766375932111f8af0d3c175582297ba749cc087efce3bf38`

## What to try

- Balanced: first touch/Home after a pause, scrolling, app switching and screen off/on. It retains E001–E005 and now uses a 200 MHz GPU wake level. Maximum CPU/GPU clocks stay available.
- Switch Performance → Power Save → Balanced. Performance retains high active frequency floors. Power Save now uses Balanced's hardware policy beneath Android Battery Saver, avoiding the old perfd cap/hint suppression. That removes one previous restriction; power savings are unmeasured.
- Check camera, audio, Wi-Fi, 65 Hz, incoming calls/SMS after screen-off, IMS and mobile data. Save/reopen a photo or document; copy a familiar file to internal/SD storage and compare checksums. Real fsync remains enabled.
- Note powered-off charging percentage, then Android percentage after boot and again after the first minute. Reporting repairs do not establish accurate calibration; the 90%/49% discrepancy is not yet hardware-verified. Do not delete batterystats or force displayed 100%.

## Optional ADB snapshot

Download `check-e007.sh` from this folder. With platform-tools available, run:

```powershell
adb push check-e007.sh /data/local/tmp/
adb shell sh /data/local/tmp/check-e007.sh > E007-Balanced.txt
```

Repeat after switching profiles, using `E007-Performance.txt` and `E007-PowerSave.txt`, or use `Collect-E007-Windows.cmd` with adb on PATH. No root is required for the main snapshot; restricted nodes are skipped.

Expected `vendor.a37.profile`: Power Save=0, Balanced=1, Performance=2. `profile_apply` and `boot_apply` should say `ok`; GPU `default_pwrlevel` should be 2 in Power Save/Balanced and 0 in Performance. A displayed GPU clock may retain its last value while clocks are off. USB-connected snapshots are not untouched idle-power measurements.

## Scope and recovery

Six independent kernel fixes cover CPU shared-policy updates, Cinnamon FIFO/read counting, GPU resume limits, VM-BMS fallback monitoring and OPPO SOC/error handling. The full ARM64 build and sanitizer/native-emulation checks passed. Battery gain, phone stability and charging accuracy remain device-test results.

The original ROM declares vm_bms but lacks its executable. The kernel fallback is repaired; a compatible daemon has not been restored. No additional undervolt, new GPU step, GPS/cellular supply change, storage clock experiment or wakelock-blocker expansion is included. CPU/GPU overclocks, original ramdisk/QCDT, camera files and Android file metadata are preserved.

If it fails to boot or regresses, reflash your working V2.1 ZIP in TWRP without formatting Data. Reinstall root/add-ons as needed. No separate boot flash is needed for the full ZIP; `boot.img` is included here only as the matching component for inspection/manual work.

[Kernel source](https://github.com/Rad-Sharkboy/kernel_oppo_A37f-For-Android-10-/tree/battery-lab/e007-bundle) · [ROM source](https://github.com/Rad-Sharkboy/OppoA37-LineageOS-17.1_Remastered/tree/battery-lab/e007-bundle) · `build-manifest.json` records exact hashes/commits.
