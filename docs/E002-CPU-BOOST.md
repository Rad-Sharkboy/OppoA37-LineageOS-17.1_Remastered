# E002: initial CPU boost target 1209.6 → 998.4 MHz

Hypothesis: lower the initial interactive boost floor to reduce energy spent on short bursts without a noticeable responsiveness loss. Maximum CPU frequency remains 1209.6 MHz. All other governor settings, GPU clock limits, GPU timeout=80 ms, 65 Hz display and radio settings stay fixed. Increased completion time or earlier subsequent boosts may erase any saving; no gain is promised.

## Prepare

Keep V2 installed; no TWRP or kernel flashing. Copy the kit's tools folder beside adb.exe. Wait at least five minutes after boot. Use comparable temperatures, brightness, network conditions and apps in both sessions.

```bat
.\adb.exe push tools/collect-baseline.sh /data/local/tmp/
.\adb.exe push tools/gpu-idle-test.sh /data/local/tmp/
.\adb.exe push tools/cpu-hispeed-test.sh /data/local/tmp/
.\adb.exe shell "su -c 'sh /data/local/tmp/gpu-idle-test.sh status'"
```

If GPU timeout is 500, apply the accepted E001 setting once:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/gpu-idle-test.sh apply'"
```

If it already reads 80, leave it alone. Any other value requires investigation. Both CPU A and B sessions must use 80. The CPU script checks the actual online CPU policy, so it also handles the observed case where CPU0 is offline.

## A: current CPU boost behavior

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/cpu-hispeed-test.sh status'"
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-baseline.sh'" > cpu-A-before.txt
```

Expect 1209600 kHz. Unplug and perform a repeatable 20-minute app-launch/scrolling sequence. Reconnect:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-baseline.sh'" > cpu-A-after.txt
```

## B: lower initial boost target

Return to a comparable starting temperature, then:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/cpu-hispeed-test.sh apply'"
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-baseline.sh'" > cpu-B-before.txt
```

Expect `E002 active: initial boost target 998400 kHz`. Unplug and repeat the same 20-minute sequence; record app-launch delay, scrolling stutter, warmth and any call/data issues. Reconnect:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/cpu-hispeed-test.sh status'"
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-baseline.sh'" > cpu-B-after.txt
.\adb.exe shell "su -c 'sh /data/local/tmp/cpu-hispeed-test.sh restore'"
```

Status should still read 998400 before restore. Send the four files and observations, including actual durations. If an override occurred, report it rather than repeatedly forcing the value. Restore immediately if responsiveness regresses. Restore changes only the CPU hispeed target back to 1209600; it does not undo the accepted GPU setting.

Reboot restores normal startup CPU tuning. The script rejects saved state from a previous boot; remove `/data/local/tmp/a37-e002-cpu-hispeed` only after verifying the normal target is back to 1209600 before a new test.

Local fixture checks passed for apply/readback/restore, offline CPU0 discovery, and refusal on changed governor/max/GPU baseline, early uptime or stale state. The experiment has not yet been run on the phone. Keep test harnesses local; the downloadable script is a phone experiment tool, not a kernel regression-test file.

## Separate idle diagnostic

At another time, leave the phone unplugged and screen off for 30–60 minutes, reconnect, then immediately run:

```bat
.\adb.exe push tools/collect-idle.sh /data/local/tmp/
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-idle.sh'" > idle-history.txt
```

The collector does not force Doze or change settings. Reconnection wakes the phone; we inspect retained idle history and flags, not just its current charging/ACTIVE state. Send this file separately; do not mix it into the screen-on CPU comparison.
