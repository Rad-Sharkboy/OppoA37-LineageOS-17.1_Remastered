# E003: hold moderate work at 998.4 MHz

**Retention:** accepted after the user's ordinary-use report. [POWER-PROFILES.md](POWER-PROFILES.md) now supplies this table in Balanced/Power Save while keeping the original table in Performance. The standalone commands below remain available for isolated comparisons.

Raise only the target load associated with the 998.4 MHz CPU step from 60% to 65%. This gives that step slightly more work before the governor chooses a higher frequency, potentially reducing power use during normal activity. The accepted initial boost stays 998.4 MHz and the maximum stays 1209.6 MHz.

Only `998400:60` becomes `998400:65` in the target-load table. Every other entry, boost timing, GPU setting, thermal setting, 65 Hz display and radio configuration stays as it was.

## Try it on the current V2

Download the updated kit and copy its `tools` folder beside `adb.exe`. Keep the accepted CPU boost=998400 and GPU timeout=80 active, and wait at least five minutes after boot. No flashing is needed.

Run in Windows Command Prompt:

```bat
.\adb.exe push tools/cpu-target-load-test.sh /data/local/tmp/
.\adb.exe shell "su -c 'sh /data/local/tmp/cpu-target-load-test.sh apply'"
```

Expect `E003 active: 998.4 MHz target load 60% -> 65%`. If the script stops on a different CPU/GPU setting or table, send its output; do not bypass the check. CPU persistence instructions are in CPU-BOOST-DEFAULT.md. GPU E001 remains temporary across reboot unless its ROM edit has been installed.

Use the phone normally: open your usual apps, type, scroll and switch apps. Screen off/on once. No fixed-duration battery run and no four-file A/B collection are required. Watch for slower launches, scrolling hesitation or delayed wake-up; higher CPU occupancy or longer completion time can offset the intended energy benefit.

When convenient, run:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/cpu-target-load-test.sh status'"
```

Send that short output and whether the phone feels the same, better or worse. The script prints the table, CPU boost and GPU timeout. It does not keep running after applying the value.

## Restore

If response gets worse:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/cpu-target-load-test.sh restore'"
```

This restores the old table only, keeping the accepted CPU initial boost and GPU timeout. Reboot also clears E003 with the existing V2 startup configuration. It may reset other temporary settings such as GPU E001. The script refuses to restore state from another boot or overwrite an unexpected table. A new apply can clear its recognized old-boot state once the exact baseline table is back.

## Why this entry

The repository's `drivers/cpufreq/cpufreq_interactive.c` uses frequency-adjusted load in `choose_freq()`. With the CPU at 998.4 MHz, an illustrative 62% sample selects 1094.4 MHz under the original table; the changed table can keep 998.4 MHz. At 70%, both select 1094.4 MHz; at 90%, both select 1209.6 MHz. Existing boost/floor/hysteresis rules still affect transitions. These are selection examples, not battery measurements.

Changing `go_hispeed_load` alone is less predictable here: bypassing its direct jump to hispeed can instead select an even higher frequency through the aggressive target-load table. Shortening boostpulse duration also needs evidence that userspace actually sends those pulses. This single table entry is a smaller next step.

The standalone experiment remains temporary. The optional profile module supplies persistence; the extracted ROM text and kernel startup tables have not yet been changed for E003. Final ROM integration will include its profile behavior as a whole.
