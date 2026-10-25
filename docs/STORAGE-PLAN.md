# Internal eMMC, SD card and reboot performance

The first device baseline contains no storage queue/mount information. `tools/collect-storage.sh` adds read-only collection of queue settings, device mapping, mount options, MMC negotiated mode/clock if debugfs exposes it, free space, dynamic-fsync state, display information and available boot timing properties. It neither enumerates personal files nor performs write benchmarks. Device logs should be shared for diagnosis, not committed wholesale.

## Source findings requiring runtime context

- **Scheduler accounting:** `block/cinnamon-iosched.c` at current kernel commit `7fb4541` stores a latency EWMA at lines 484–493, then divides it by request count again in adaptation near line 527 and reporting near line 921. For example, a 100 ms EWMA divided by count 100 becomes an apparent 1 ms. This is an isolated correctness-fix candidate; it is not yet a demonstrated phone-speed improvement. The flashed kernel is a dirty build, so source equivalence remains limited.
- **Write durability:** `fs/sync.c:228` bypasses fsync when `dynamic_fsync=1`; delayed work in `kernel/power/cinnamon_delay_trigger.c:435` can enable it while discharging above 30%, revisiting every 60 seconds. V2's `fstab.qcom` includes `barrier=0,noauto_da_alloc,journal_async_commit,commit=20` for data/cache. Read the actual mount and proc settings before assuming these policies are active. Never count a skipped flush as a storage improvement. USB connection changes charging state and may therefore also change dynamic-fsync behavior between benchmarks.
- **Overrides:** kernel boot work requests Cinnamon and 512 KB read-ahead. ROM `lineage-iosched.rc` applies scheduler properties to both internal and removable storage. Later tests must target one identified queue and check its effective setting; changing a shared property does not isolate the devices.
- **Adaptive read-ahead:** Cinnamon already changes it between 128 and 2048 KB according to its own heuristics. Bigger read-ahead is not automatically faster and can waste RAM and I/O. Confirm effective settings before/after each workload.
- **Prior storage OC failure:** CHANGELOG.md records an HS400/200 MHz eMMC and DDR50 SD experiment that bootlooped and was reverted. Keep existing negotiated clocks/modes; do not repeat generic storage overclock recipes.

## Next sequence

1. Complete GPU E001 separately; collect storage snapshots while doing so, but apply no I/O changes.
2. Identify the live scheduler and internal/SD backing devices. Reconcile fsync/mount behavior before interpreting write-speed tests.
3. Consider the scheduler arithmetic fix as its own source commit, with deterministic arithmetic checks and kernel build validation. Preserve CPU/GPU clocks, the 65 Hz display setting, thermals and telephony. A test boot image must preserve V2's legacy boot format/ramdisk/DT metadata and account for its dirty-kernel baseline; do not substitute the onboarding build as a proven equivalent.
4. Compare repeated identical app launches and copies, plus foreground scrolling during background copying. Verify copied-file hashes. Use an explicit disposable test directory with enough free space; never write a benchmark to a raw block device. Report throughput and responsiveness separately.
5. Time shutdown, boot to unlock screen, and boot to interactive app launch separately under the same conditions. Sequential I/O throughput does not establish faster reboot. Do not skip shutdown flushes or shorten critical service timeouts just to improve the stopwatch result.

No storage improvement, SD-card compatibility, or reboot-time reduction has been validated on hardware yet. Clock increases and changes that weaken durability are not part of this plan.
