# Balanced battery tuning and Performance frequency floors

This optional Power HAL patch connects the accepted battery settings to the phone's actual **Settings → Battery saver and performance → Performance profile** selection. Balanced uses the lower boost/shorter GPU delay; Performance raises the CPU and GPU minimum frequencies to their current allowed maximums. Power Save releases those high floors and retains the original HAL's power-saving restrictions.

| Setting | Balanced / Power Save | Performance |
| --- | --- | --- |
| CPU minimum | 200 MHz, subject to existing restrictions | Current allowed maximum, normally 1209.6 MHz |
| GPU minimum | 200 MHz, subject to existing restrictions | Current devfreq ceiling, normally 620 MHz |
| Interactive initial boost | 998.4 MHz | 1209.6 MHz |
| Target-load entry at 998.4 MHz | 65% (E003) | Original 60% |
| GPU idle delay | 80 ms (E001) | Original 500 ms |

Performance intentionally spends more power to keep active clocks high. Frequency floors do not keep an idle CPU/GPU awake: hardware sleep and thermal protection still operate. Existing maximum clocks, the 65 Hz screen, radio/IMS configuration, input boosting and E004's idler counter are unchanged. The patch clamps each floor to the maximum exposed by its frequency control. KGSL's separate thermal cap also takes priority, so the GPU can run below its reported devfreq floor when throttled.

Select Balanced before lowering GPU maximums with another tuning app: this old devfreq interface rejects a maximum below its requested minimum. V2's thermal-engine uses a separate control and remains effective.

## First finish the short E005 comparison

The first-touch/Home delay has its own test in [E005-FIRST-TOUCH.md](E005-FIRST-TOUCH.md). Try that in Balanced before installing this profile patch, so you can tell whether the small input pulse helps. No long timed battery run is needed. Installation below reboots the phone and therefore clears temporary E005; reapply it afterward only if you chose to retain it.

## Install on the current V2

This is an experimental native Power HAL extension, packaged as a reversible Magisk module. It needs **one reboot**, with no ROM reinstall or TWRP flash. The installer accepts only the exact original V2 Power HAL and checks the generated file's hash before activating the overlay. The original ROM partition remains intact.

Download the latest [test kit](https://github.com/Rad-Sharkboy/OppoA37-LineageOS-17.1_Remastered/raw/refs/heads/battery-lab/v2-baseline-e001/downloads/A37-V2-test-kit.zip), extract it, and copy its `tools` folder beside `adb.exe`. Run in Windows Command Prompt:

```bat
.\adb.exe push tools/power-profile-bridge /data/local/tmp/
.\adb.exe shell "su -c 'sh /data/local/tmp/power-profile-bridge/install.sh install'"
```

Continue only if it prints `Profile bridge installed`. A different original HAL, unknown older startup helper or existing module causes a refusal; send that output instead of bypassing it.

```bat
.\adb.exe reboot
```

Use the phone normally. After roughly six minutes, select **Performance**, then collect. If Performance was already selected, choose Balanced first so the switch generates a new profile event:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/power-profile-bridge/install.sh status'" > profile-performance.txt
```

Select **Balanced**, then collect:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/power-profile-bridge/install.sh status'" > profile-balanced.txt
```

The active profile should change from `2` to `1`, the last HAL write result should be `ok`, and the CPU/GPU minimums should follow the table. Briefly turn the screen off/on and check that Balanced still responds normally. Send those two small files and whether touch/Home, app switching and wake-up feel normal. If `incomplete` appears or the values disagree, send the output; do not manually force maximums to hide it.

The one-time five-minute boot reconciliation handles the old V2 kernel's delayed settings writes. It then exits. Profile and screen events apply settings directly through the HAL; there is no resident shell polling loop. A recognized older E002 startup helper is backed up and replaced by this profile-aware mechanism so it cannot lower the Performance boost later.

E003 is retained here following the user's no-slowdown feedback. The last pasted E003 output showed the baseline table and reset GPU/CPU values, so the profile readback above also establishes what is actually active. Those commands were run in Balanced; the screenshot's Performance selection does not explain their values.

## Roll back

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/power-profile-bridge/install.sh remove'"
.\adb.exe reboot
```

This removes the overlay and restores the recognized older E002 helper if one was backed up. Other temporary experiments reset according to their normal boot behavior. You can also remove **A37 Balanced and Performance Profiles** in Magisk and reboot.

If Android cannot start normally, disable this module using Magisk's module recovery procedure or, when root ADB is available:

```bat
.\adb.exe shell "su -c 'touch /data/adb/modules/a37_power_profiles/disable'"
.\adb.exe reboot
```

With `/data` accessible in TWRP, its file manager can remove just `/data/adb/modules/a37_power_profiles` to disable the overlay. No data wipe is required. That emergency removal does not restore the module's backup of the old E002 helper; it can be reinstalled separately later.

The patch passed host ARM64 emulation and local packaging checks. Android's real linker, HAL service, performance daemon and drivers still need this device check. This is separate from the eventual ROM-kitchen replacement package; do not copy the whole tools folder into the ROM.
