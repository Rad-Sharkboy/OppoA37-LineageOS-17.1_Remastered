# Start here: current tests and V2 baseline

**E001–E005 are accepted:** the user reports all five applied and working. E004's three idle checks and E005's 800 MHz / 40 ms input boost are now retained in the development ROM init file. They remain temporary on the installed V2 until the edited files are packaged; there is no need to repeat the comparisons.

**Then profile-aware tuning:** `docs/POWER-PROFILES.md` explains the optional Magisk Power HAL extension: accepted battery settings in Balanced, high CPU/GPU floors in Performance. It needs one reboot and a short profile-switch check. E003 is retained in this mechanism following ordinary-use feedback. `docs/CHANGE-STATUS.md` tracks final packaging.

**E006 and kernel cleanup:** `docs/E006-KERNEL-WORK.md` describes the scheduler work reduction, zRAM cleanup and debug/profiling reductions. E006 requires a rebuilt kernel; there is no ADB apply command. The ROM ZIP remains unassembled for now, with a later combined install check described there.

The baseline steps below are for first-time collection; no repeat baseline or timed battery test is required for a phone already reviewed. `docs/CPU-BOOST-DEFAULT.md` describes the older CPU-only helper; the new profile module replaces a recognized copy automatically.

Keep the V2 ROM and kernel already installed on your phone. Do not reinstall the ROM, flash this ZIP, use TWRP, or apply the GPU experiment for this first step. This ZIP contains scripts and documentation, not a flashable update.

## 1. Prepare the computer and phone

1. Download `A37-V2-test-kit.zip` and extract it on your computer.
2. Use your existing Android platform-tools folder (the folder containing `adb.exe`). If needed, download Google's Windows platform-tools: https://dl.google.com/android/repository/platform-tools-latest-windows.zip
3. Copy the extracted kit's `tools` folder into the platform-tools folder. You should now have `adb.exe` alongside `tools/collect-baseline.sh`.
4. On the phone, enable **Developer options → USB debugging**, connect USB, unlock the screen, and accept the USB debugging authorization prompt.
5. Wait until the phone has been running for at least five minutes after its last boot. No new reboot is required.
6. Open Command Prompt in the platform-tools folder: open that folder in File Explorer, type `cmd` in its address bar and press Enter.

## 2. Check ADB and root

Run each command separately:

```bat
.\adb.exe devices
```

The phone should appear with status `device`. If it says `unauthorized`, accept the prompt on the phone and retry. If no phone appears, check the cable, USB debugging and the phone's Windows ADB driver before continuing.

```bat
.\adb.exe push tools/collect-baseline.sh /data/local/tmp/
.\adb.exe shell su -c id
```

Approve the shell's root request on the phone if prompted. `uid=0(root)` means the rooted collection command below can be used. If `su` is missing or permission is denied, use the non-root alternative; do not install or flash anything just for this collection.

## 3. Save the baseline

If the root check succeeded:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-baseline.sh'" > baseline-before.txt
```

If root is unavailable, use this command instead:

```bat
.\adb.exe shell sh /data/local/tmp/collect-baseline.sh > baseline-before.txt
```

The collection may take several seconds. The `>` saves the output into `baseline-before.txt` in the computer's platform-tools folder, so little or nothing may appear in the terminal. Open the file and check that it contains `A37 battery study snapshot v1` followed by device information. If it contains only an error, send that error instead.

Send `baseline-before.txt` in chat. This snapshot reads configuration and counters; it does not tune or flash the phone. The script copied into `/data/local/tmp` is just a local diagnostic file.

## What happens next

We first check CPU frequency limits and governor settings, GPU timeout and frequency limits, low-power-mode state, and battery/wakelock readings. The next test depends on those actual values. A single snapshot does not measure battery drain.

The optional `gpu-idle-test.sh` in the kit is for a later, explicitly described A/B comparison. Do not run `apply` yet. Nothing needs flashing in TWRP for that runtime experiment either.

If your baseline has already been reviewed and E001 has been recommended, follow `docs/E001-RUN-WINDOWS.md` in the kit. The first A37fw baseline is summarized in `docs/BASELINE-RESULTS.md`.

E001 GPU timeout=80 ms and E002 CPU initial boost=998400 kHz are now accepted. `docs/CPU-BOOST-DEFAULT.md` describes installing CPU persistence on the current rooted V2. `docs/GPU-80MS-DEFAULT.md` describes retaining 80 ms in an edited ROM; saving either change on GitHub does not install it on the phone.
