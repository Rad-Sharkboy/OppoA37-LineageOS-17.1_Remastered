# First device baseline: 25 October 2026

Summary of the user-supplied snapshot only. The raw device log is not published.

| Observation | Meaning |
| --- | --- |
| Root works; uptime about 490 seconds; build #408, g6230b382fc7-dirty | Delayed boot tuning had time to run; matches V2's embedded version string. |
| `vendor.post_boot.parsed=1`; `sleep_disabled=N` | ROM low-power setup ran; the cmdline sleep-disable flag is not active now. |
| CPU min/max 200000/1209600 kHz; time-in-state includes 200000 | The minimum-frequency fix works in this sample. A momentary max-frequency reading does not mean a stuck CPU. |
| cpuidle `pc` state has entries and recorded time | CPU power-collapse idle is used; this does not establish total suspend residency or good overnight drain. |
| `hispeed_freq=1209600`, `go_hispeed_load=75`, aggressive stepped target loads | Confirms several kernel delayed overrides; `io_is_busy` remains 0, so not every kernel default wins. |
| GPU available/min/max: 200/310/620 MHz; idle timeout 500 ms; idler=1; force-on knobs=0 | E001's required 500 ms baseline is present. Do not lower overclock limits for this experiment. |
| Charging; battery temperature 464 (46.4 C) | Useful configuration snapshot, unsuitable as an unplugged drain comparison. Cool before A/B testing. |
| Battery capacity 64%, BMS capacity 52%, BMS current 0 | Exposed battery providers disagree; current and percentage alone cannot establish energy gains. |
| `radio-interface`, `qcril`, `ims_socket_wake` present in blocker | Existing telephony blocking is active as a list. It does not prove a call failure; preserve functionality and test incoming calls after standby. |
| Approximately 532 MiB free RAM, 643 MiB page cache, no swap used | No evidence of memory pressure in this one snapshot. Page-cache removal is not a demonstrated improvement. |

Frequency counters include boot and USB-connected activity; do not use their lifetime percentages as a controlled workload result. GPU frequency samples alone do not establish power/clock residency. The 65 Hz LCD overclock is a user-confirmed requirement, not a setting measured by the first collector.

Next: E001 GPU timeout comparison, with clocks and display settings unchanged; separately collect storage/display state with `tools/collect-storage.sh`. Do not combine an I/O change with E001. See E001-RUN-WINDOWS.md.
