# E001: first hardware result

Subsequent user decision: retain 80 ms as the preferred setting despite unmeasured energy savings; see GPU-80MS-DEFAULT.md. The assessment below records the initial test evidence.

User ran A/B on V2, reported no noticeable slowdown, and supplied all five requested snapshots. Snapshots reconnect over USB and therefore report charging, as expected. Raw device logs are not published; this is a derived summary.

| Measurement | A: 500 ms | B: 80 ms |
| --- | --- | --- |
| Timeout at both endpoints | 500 / 500 ms | 80 / 80 ms |
| Snapshot-to-snapshot elapsed interval | 366.11 s (6m06s) | 467.97 s (7m48s) |
| Reported battery temperature | 44.5 → 45.7 C | 45.7 → 45.4 C |
| Displayed battery percentage | 64 → 60 | 60 → 53 |
| GPU frequency-accounting delta at 620 MHz | 114.147 s | 128.780 s |
| At 310 MHz | 195.516 s | 141.210 s |
| At 200 MHz | 56.396 s | 76.137 s |
| Sum of GPU frequency-accounting deltas | 366.059 s | 346.127 s |
| Frequency transitions | 129 | 138 |

## Conclusion

- E001 applied successfully and was still active at the B endpoint. This and the user's no-slowdown report are a preliminary compatibility result.
- Battery benefit is **unproven**. Runs differ in duration, start temperature and battery state; no app frame-time history or controlled-workload record was supplied. Percentage drop per minute is not a reliable energy comparison with this gauge and USB endpoint handling.
- The GPU statistics use jiffies-based bookkeeping in `drivers/devfreq/devfreq.c`; they are not a rail-power or clock-on meter. B's accounted total is about 122 seconds shorter than its elapsed interval. Suspend/timebase behavior, different activity and unaccounted time cannot be attributed uniquely to the timeout change. Do not label that gap as energy saved.
- CPU0 was offline in some snapshots; CPU-frequency information appears under the online CPU (for example CPU2). This is not a missing-collector failure. Do not add duplicated shared-policy time-in-state counters across cores.
- A claimed device thermal maximum does not establish equal test conditions or measured efficiency. No thermal-limit changes are part of E001.

Keep E001 as an optional reversible experiment, not an established permanent optimization. It remains reasonable to test 80 ms for longer matched use, with the same brightness, 65 Hz display setting, network conditions and workload, and to check standby calls/SMS and display wake. Restore 500 ms if regressions appear. Use the existing apply/restore script and E001-RUN-WINDOWS.md; do not combine this with an I/O tuning experiment.

## Storage snapshot conclusions

- Internal storage is `mmcblk0` (MMC); removable storage is `mmcblk1` (SD). Both have Cinnamon selected.
- Read-ahead values are 704 KB internal and 256 KB SD in this snapshot. These are observations, not recommended targets; Cinnamon adapts them.
- `/proc/dynamic_fsync` is 0 **at the charging snapshot**. This does not establish its unplugged setting because existing delayed work can change it.
- `/data` and `/cache` actually use `nobarrier,noauto_da_alloc,journal_async_commit,commit=20`. Existing write-durability choices must be accounted for in future storage benchmarks.
- The sampled MMC debug state reports clock 0/power off. This is not evidence that transfers run at zero clock or that a clock increase is needed. Query an active workload before inferring the negotiated mode/rate.
- The display snapshot does not independently report 65 Hz; the user's working 65 Hz setting remains a preservation requirement. No display change was made.

The scheduler EWMA correction is the next isolated source fix, with host regression and ARM64 object-build checks. A replacement boot image is not part of this results report; V2's dirty kernel and legacy boot layout still need a controlled compatibility baseline before kernel A/B testing.
