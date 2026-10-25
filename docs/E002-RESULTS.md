# E002 CPU boost observations

The user accepted `hispeed_freq=998400` after ordinary use without noticeable responsiveness loss. Keep this target and prioritize drain during active use over further idle experiments. No repeat of a long controlled test is required for this retention decision.

## Uploaded snapshots

| Observation | A | B |
| --- | ---: | ---: |
| Initial boost target, both endpoints | 1209600 kHz | 998400 kHz |
| Elapsed interval | 98.24 s | 169.53 s |
| CPU minimum / maximum | 200000 / 1209600 kHz | 200000 / 1209600 kHz |
| GPU idle timeout | 80 ms | 80 ms |
| Accounted CPU time at maximum | 68.45% | 32.26% |
| Accounted CPU time at 200 MHz | 22.97% | 41.98% |
| Battery sensor temperature | 43.7 → 44.4°C | 44.6 → 44.7°C |

B still used maximum frequency. The lower initial boost held at both endpoints and the user reported no slowdown. The counters show less time at maximum in B; different short workloads mean that the size of this difference cannot be attributed entirely to the setting.

Frequency residency uses one complete shared-policy snapshot per endpoint, not the sum of all cores: CPU0 → CPU2 for A and CPU1 → CPU1 for B. Shared-policy counters are exposed under whichever CPUs are online. The accounted totals are 99.46 s and 169.54 s; collection is sequential, so it is not an atomic snapshot. These counters describe frequency residency, not energy.

USB was connected at collection endpoints, as expected. Battery capacity remained 56% while the BMS percentages differed and current readings were zero. These snapshots cannot quantify the battery saving; they establish setting readback and ordinary-use acceptance.

## Idle diagnostic

The retained history shows repeated light Doze and maintenance cycles over roughly 83 minutes before unlocking. Its current ACTIVE/charging state follows reconnection and is expected. Deep Doze is enabled, but this history contains no deep-idle entry; `mUseMotionSensor=true` with `mMotionSensor=null` is a possible later framework/sensor lead, not evidence that kernel sleep is broken.

Wi-Fi always-scanning is already 0. A null scan-throttle setting means the framework default, not that throttling is disabled. Leave those settings unchanged. The user reports that normal-use drain matters more than idle drain, so further deep-idle investigation is deferred.

See [CPU-BOOST-DEFAULT.md](CPU-BOOST-DEFAULT.md) for the retained setting and simple installation/rollback steps.
