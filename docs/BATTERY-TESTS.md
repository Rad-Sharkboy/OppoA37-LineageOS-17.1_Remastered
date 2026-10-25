# Baseline and E001: GPU idle timeout

E001 GPU timeout=80 ms and E002 CPU hispeed=998400 kHz have since been accepted for retention based on ordinary-use feedback. The comparison plan below describes the original exploration; longer controlled tests are optional, not a requirement to keep these accepted settings. See GPU-80MS-DEFAULT.md and CPU-BOOST-DEFAULT.md for current instructions.

No battery gain has been measured yet. These scripts are for a rooted Oppo A37/A37f/A37fw running the confirmed V2. They do not flash or change boot files.

## Collect the baseline first

Wait five minutes after boot so delayed kernel tuning has run. From a computer with ADB:

```sh
adb push tools/collect-baseline.sh /data/local/tmp/
adb shell su -c 'sh /data/local/tmp/collect-baseline.sh' > baseline-before.txt
```

If `su` is unavailable, run `adb shell sh /data/local/tmp/collect-baseline.sh` instead; inaccessible nodes remain unavailable, and the write experiment must wait for root. Send the baseline before attributing drain to any particular setting.

Take a second snapshot after each test (`baseline-after.txt`). This is a one-shot collector: do not poll continuously, since polling, an attached USB cable and ADB traffic change idle behavior. Unplug for the test interval. USB reconnection wakes the device and may charge it, so readings taken then are endpoints, not untouched standby measurements. Record start/end times and reconnect consistently.

## E001 proposal

Hypothesis: a 500 ms GPU idle tail wastes energy between short UI bursts. Shortening it to 80 ms may improve light-use battery life without lowering clock limits. It may instead increase sleep/wake transitions or cause frame-time spikes. Sustained GPU-heavy gaming may show little benefit.

Only run after saving the baseline. The script requires root, at least five minutes uptime, and a current timeout of exactly 500 ms. Unexpected values cause it to stop.

```sh
adb push tools/gpu-idle-test.sh /data/local/tmp/
adb shell su -c 'sh /data/local/tmp/gpu-idle-test.sh status'
adb shell su -c 'sh /data/local/tmp/gpu-idle-test.sh apply'
```

This changes one sysfs value to 80 ms and checks readback. CPU/GPU clocks, voltage tables, thermal policy and radio/IMS files remain untouched. Read `status` again after screen-off/on and after the workload to detect overrides.

Rollback immediately if wake-up stutter, rendering faults, crashes or unusual heat appear:

```sh
adb shell su -c 'sh /data/local/tmp/gpu-idle-test.sh restore'
```

A reboot restores normal startup settings. After reboot, the saved state is intentionally rejected; remove the stale directory before another experiment using `adb shell su -c 'rm -r /data/local/tmp/a37-e001-gpu-idle'` only when you have verified the normal timeout is back to 500 ms.

## Comparison

- Run A (500), B (80), A (500), B (80), with the same brightness, radio/network conditions, apps, workload, initial temperature and comparable battery state. Allow cooling between sessions. Change one setting at a time.
- For light use, repeat the same 20–30 minute scrolling/app-switching sequence. Record app-launch delay, visible stutter, temperature and available GPU residency/busy counters. Use `collect-baseline.sh PACKAGE_NAME` after the same sequence to include that app's `dumpsys gfxinfo` frame history; it is a rolling buffer, not a full-session benchmark. Compare frame-time distributions and missed-frame counts, not just averages.
- For idle, compare equal 1–2 hour unplugged screen-off periods, then a longer overnight repeat if stable. Keep SIM/network/Wi-Fi conditions matched. Compare cpuidle and wakeup-counter deltas where exposed. CPU frequency time-in-state alone is not a deep-sleep measurement.
- Verify incoming calls and SMS after 15–30 minutes screen-off, call audio, reconnection to mobile data and normal IMS/VoLTE behavior where supported by your carrier. Do not test emergency numbers.
- Battery percentage and this kernel's reported current are not trustworthy energy instruments. Record them as observations, not proof. Voltage is also affected by load, temperature and rebound. Longer controlled runtime tests help; an external calibrated battery power measurement is stronger. A USB charging meter measures input energy, not directly battery discharge, and auto-bypass/charging losses complicate it.
- Keep E001 only if repeated B runs show improvement beyond run-to-run variation with acceptable responsiveness and stable functionality. Otherwise restore A. No promised percentage improvement or performance equivalence.

Cloud validation covers extraction integrity and script behavior against fixtures. Device stability, real sysfs access, wake latency, call behavior and battery benefit remain untested until the user runs these tests.
