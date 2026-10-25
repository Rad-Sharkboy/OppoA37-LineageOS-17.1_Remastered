# Broader Android power research, applied to V2

Sources were fetched and read on 25 October 2026. These are general Android/kernel mechanisms, not Oppo A37 forum recipes or reports of guaranteed gains. Version-specific claims below are checked against Android 10 source or the legacy interactive governor used here.

## 1. Initial CPU boost target: next isolated experiment

[Android's kernel governor documentation](https://android.googlesource.com/kernel/msm/+/android-msm-bullhead-3.10-marshmallow-dr/Documentation/cpu-freq/governors.txt) states that lower `target_loads` makes interactive raise CPU speed more often. `hispeed_freq` is an intermediate boost target; it is not the maximum frequency cap. `boostpulse_duration` defines how long a boost pulse holds at least that target. Sampling uses a deferrable timer, so simply doubling `timer_rate` is not proof of halving idle wakeups.

The live V2 baseline has hispeed=1209600, go_hispeed_load=75 and aggressive stepped target loads, despite ROM requests for 800000/95 and gentler loads. Kernel delayed tuning is confirmed to override several values.

E002 changes **only hispeed_freq: 1209600 → 998400 kHz**. It is accepted for retention after ordinary-use feedback. Keep scaling_max_freq=1209600, the existing target-load table, GPU timeout=80 ms, clocks and 65 Hz unchanged. This intermediate target may reduce burst energy, but longer active time can offset lower frequency and aggressive target loads can still raise it to maximum. See CPU-BOOST-DEFAULT.md.

## 2. Verify Doze, not just CPU idle

[AOSP platform power management](https://source.android.com/docs/core/power/platform_mgmt) and [Android's Doze/App Standby guidance](https://developer.android.com/training/monitoring-device-state/doze-standby) describe batching background work into maintenance windows. Full Doze versus light Doze depends on platform integration and motion capabilities. A CPU entering a power-collapse state does not prove Android's app-idle policy is functioning.

Our logs do not yet include `dumpsys deviceidle`. The [Android 10 DeviceIdleController](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/android10-release/services/core/java/com/android/server/DeviceIdleController.java) exposes `Idling history` and light/deep enabled flags. After an unplugged screen-off period, reconnect and immediately run `collect-idle.sh`. Reconnection may show current ACTIVE/charging; inspect retained history instead of calling that a Doze failure. If the history is absent or truncated, that is inconclusive.

V2 explicitly exempts IMS packages in qti_whitelist.xml. Preserve those and other necessary communication exemptions. Investigate specific repeated background wakeups before changing timers or exemptions.

## 3. Android 10 Wi-Fi scan throttling

[Official Wi-Fi scan guidance](https://developer.android.com/develop/connectivity/wifi/wifi-scan) describes Android 10's foreground limit of four scans in two minutes and a combined background limit of one scan in 30 minutes, with privileged exceptions. [Android 10 ScanRequestProxy](https://android.googlesource.com/platform/frameworks/opt/net/wifi/+/refs/heads/android10-release/service/java/com/android/server/wifi/ScanRequestProxy.java) defaults `WIFI_SCAN_THROTTLE_ENABLED` to 1.

Read `settings get global wifi_scan_throttle_enabled` before tuning. A missing/null setting does not mean disabled: the source uses an enabled default. If explicitly disabled, enabling it is a candidate only after checking the user's Wi-Fi diagnostic/scanning needs. Existing legacy scan-interval properties do not establish that app scan requests are throttled.

## 4. Existing WLAN power saving: already present

The original V2 `WCNSS_qcom_cfg.ini` already includes IMPS=1, BMPS=1, idle scanning disabled, suspend mode=3, beacon early termination enabled and modulated DTIM=3. Generic advice to enable these is redundant. Increasing DTIM further can change packet/notification latency and needs its own test; it is not a default recommendation.

The editable-file import initially omitted `.ini` files. The existing Wi-Fi configuration is now imported byte-for-byte from the checksum-verified V2 image; it has not been tuned. Runtime driver behavior can still differ from configuration intent.

## Priority

Keep accepted GPU timeout=80 and CPU initial boost=998400. E002 normal-use results are in E002-RESULTS.md; the user accepted the change without noticeable slowdown. Light Doze is working, and normal-use drain is now the priority. Next candidates are the aggressive interactive target-load table and kernel work during active use; isolate any proposed change and explain it first. Do not reduce the working display refresh rate, block telephony wakelocks further, or count disabled write durability as a speed improvement.
