# E001 after baseline review: GPU idle timeout

The first baseline from the user's Oppo A37fw confirms root, V2 build #408, and a 500 ms GPU idle timer. Keep V2 installed. No TWRP, boot image, ROM reinstall or reboot is required. Preserve the working 65 Hz LCD overclock and CPU/GPU frequency limits. Only the GPU idle timeout changes.

This is an experiment, not a proven battery improvement. Shorter idle tails may save energy between UI bursts; more sleep/wake transitions may cause stutter or offset the saving. Test light use first; do not change storage settings during it.

## Prepare

Download/extract the updated kit, copy its tools folder beside adb.exe, and open CMD there. The supplied baseline was charging at 46.4 C: disconnect and let the phone return to its normal cool idle temperature before comparing sessions. Keep brightness, 65 Hz refresh, network/SIM conditions and apps the same. Use an existing offline app/content where practical to reduce network variation.

```bat
.\adb.exe push tools/collect-baseline.sh /data/local/tmp/
.\adb.exe push tools/gpu-idle-test.sh /data/local/tmp/
.\adb.exe push tools/collect-storage.sh /data/local/tmp/
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-storage.sh'" > storage-before.txt
.\adb.exe shell "su -c 'sh /data/local/tmp/gpu-idle-test.sh status'"
```

The last command should report 500 ms. If it does not, stop and send the output. The storage script only reads settings; it also captures available display information.

## A: unchanged 500 ms

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-baseline.sh'" > gpu-A-before.txt
```

Unplug USB. Perform a repeatable 20-minute sequence: for example, the same scrolling, app opening/switching and short idle gaps. Record what you did, start/end times, brightness, battery level, stutter and warmth. Reconnect only to collect:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-baseline.sh'" > gpu-A-after.txt
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-storage.sh'" > storage-A-after.txt
```

## B: 80 ms

Let the phone cool back to a comparable temperature, then connect briefly and run:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/gpu-idle-test.sh apply'"
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-baseline.sh'" > gpu-B-before.txt
```

Expect `E001 active: 80 ms`. Unplug and repeat the same 20-minute sequence. Reconnect and collect:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/gpu-idle-test.sh status'"
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-baseline.sh'" > gpu-B-after.txt
.\adb.exe shell "su -c 'sh /data/local/tmp/collect-storage.sh'" > storage-B-after.txt
```

The timer must still be 80 ms; otherwise note the override and do not attribute results to E001. Send these text files and your observations. We can first inspect changes and then repeat A/B to estimate normal variation. Twenty minutes screens for responsiveness/obvious regressions; it does not prove a battery-runtime improvement, especially with this battery gauge.

For frame data, the collector also accepts the package name of the app used for the sequence; e.g. `sh /data/local/tmp/collect-baseline.sh com.android.settings`. gfxinfo is app-specific and its history is bounded. Keep the same app and sequence in A and B.

## Restore

Restore after the first comparison while we review the results, or immediately if rendering, wake-up responsiveness or stability regresses:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/gpu-idle-test.sh restore'"
```

Expect `Restored 500 ms`. Reboot is another rollback if the script cannot run. Do not auto-apply E001 at boot. Before keeping it for longer tests, also check incoming calls/SMS after screen-off, normal mobile data/IMS behavior and display wake-up. See BATTERY-TESTS.md for longer idle comparisons and measurement caveats.
