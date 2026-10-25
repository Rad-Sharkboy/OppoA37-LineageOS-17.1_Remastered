# Start here: collect the existing V2 baseline

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

After accepting E001, keep GPU timeout at 80 ms and use `docs/E002-CPU-BOOST.md` for the next single-setting CPU comparison. `docs/GPU-80MS-DEFAULT.md` describes retaining 80 ms in an edited ROM; saving that file on GitHub does not install it on the phone.
