# E006 and the V2.1 combined kernel test

E001–E005 are accepted following the owner's ordinary-use report. E004's three GPU idle checks and E005's 800 MHz / 40 ms input pulse are retained in the edited ROM init file. E006 now moves into kernel code: it removes work that the configured interactive build does not use. It has no ADB apply command.

These changes are compiled and packaged in the complete V2.1 ROM ZIP. See [V2.1 installation and rollback](V2.1-INSTALL.md). Each source change remains in a separate commit for focused follow-up or rollback; local test harnesses and development notes are excluded from the ROM payload.

## E006: remove unused estimator updates

The abandoned schedutil experiment left UTIL_EST state updates in CFS task enqueue/dequeue and sleep paths. The only source consumer of `sched_cpu_util()` is that governor. The ARM64 source configuration has schedutil disabled and uses interactive, which does not consume this estimate.

The change compiles those fields, updates and exported helper only when schedutil is enabled. HMP's original load tracking and interactive's decisions remain. The optional governor still builds both built-in and modular; its Kconfig dependency now expresses its existing requirement for `SCHED_FREQ_INPUT`/HMP.

Local fixtures extracted the actual helpers and call sites and exercised 200,000 enqueue/dequeue events per configuration. Enabled built-in/module results were identical; the disabled case eliminated 80,040 estimator-specific `task_load()` evaluations in that fixture. GCC 4.9 ARM64 compilation passed for disabled, built-in and modular configurations. Before the separate debug trim, `kernel/sched/fair.o` text decreased by 304 bytes. These are code/work measurements, not a battery-runtime percentage.

V2's embedded dirty kernel advertises schedutil enabled, whereas the maintained source defconfig already disables it. This change targets the source build; the original installed kernel is not a byte-identical reference. Keep its boot image for rollback.

Commit: [74903107099](https://github.com/Rad-Sharkboy/kernel_oppo_A37f-For-Android-10-/commit/74903107099).

## Other independent changes

| Change | Why it helps / tradeoff | Commit |
| --- | --- | --- |
| Limit zero/repeated-byte run history writes to four slots | The ring has only four entries; additional identical writes are redundant. Compressed format and final ring state remain identical. | [89e54de2af8](https://github.com/Rad-Sharkboy/kernel_oppo_A37f-For-Android-10-/commit/89e54de2af8) |
| Validate zRAM run lengths, delta offsets and compression block size | Reject malformed decoded writes outside a page/block; unsupported tunable sizes fall back before division or history access. Adds required bounds checks. | [ea245232f6d](https://github.com/Rad-Sharkboy/kernel_oppo_A37f-For-Android-10-/commit/ea245232f6d) |
| Disable optional dynamic debug | Removes per-site metadata and enable-flag checks. Ordinary error logs, printk, tracing and debugfs remain; individual debug-print sites can no longer be enabled through `dynamic_debug/control`. | [2c98510a897](https://github.com/Rad-Sharkboy/kernel_oppo_A37f-For-Android-10-/commit/2c98510a897) |
| Disable optional MMC profiling | Removes profiling flags/counters and per-host storage. The counters were normally off; this does not imply a large I/O throughput gain. Clock scaling, transfer modes, durability and normal I/O statistics remain. | [ccc7a0b5cf8](https://github.com/Rad-Sharkboy/kernel_oppo_A37f-For-Android-10-/commit/ccc7a0b5cf8) |
| Restore actual fsync completion | Removes the custom bypass and its requeued 60-second battery-polling work. Requested saves now reach the filesystem and return its result. Real save latency can increase compared with skipping the operation. | [e0c4a41f83c](https://github.com/Rad-Sharkboy/kernel_oppo_A37f-For-Android-10-/commit/e0c4a41f83c) |

The fsync issue was established in source: above 30% battery while neither charging nor full, the worker could enable a shortcut returning success from `vfs_fsync_range()` without calling the filesystem. This affects fsync, fdatasync and callers using that helper for synchronous writes. It is not safe batching. Earlier phone captures did not record that toggle, so they do not establish its live state on the dirty V2 kernel. The repair preserves save correctness rather than claiming a performance improvement.

The zRAM run-history comparison covered 13,096 round trips at 16/32/64-byte block sizes across generic and batched control flow. Compressed bytes and final history states matched exactly; history writes fell from 950,608 to 123,498 in the corpus. Every ring start index and run length 1–256 was checked separately. NEON primitives used equivalent host stand-ins; the actual ARM64 code is covered by compilation and still needs the phone run.

Bounds validation passed 5,099 cases under AddressSanitizer/UBSan: valid and invalid runs, every delta-offset position, zero lengths, 5,000 checksummed malformed streams and supported/unsupported compression sizes. Output canaries stayed intact. The original decoder reproduced beyond-page writes in malformed test cases; this is not evidence that normal compression generated corrupt streams.

The sync regression uses the actual `vfs_fsync_range()` body: the original bypass failed eight callback/error-forwarding cases, while the repair passed. Hardware write durability is not inferred from that host fixture.

## Debloat boundaries

The full GCC 4.9 ARM64 `Image.gz-dtb` build completed successfully at kernel commit `ea245232f6d`. The comparison below uses a freshly linked source baseline at `b7a7afb407f`, with the same toolchain and all configuration symbols unchanged except `DYNAMIC_DEBUG` and `MMC_PERF_PROFILING`. It compares source builds, not the dirty kernel originally shipped in V2. Build identification/timestamps also differ, so compressed byte totals are measurements of these artifacts rather than an isolated per-option benchmark.

| Artifact | Before | After | Reduction |
| --- | ---: | ---: | ---: |
| Raw ARM64 Image | 19,531,664 bytes | 17,876,368 bytes | **1,655,296 bytes** |
| Image.gz | 7,918,435 bytes | 7,375,358 bytes | **543,077 bytes** |
| Image.gz-dtb | 8,125,912 bytes | 7,582,835 bytes | **543,077 bytes** |

The appended device-tree bytes are identical before/after (207,477 bytes, SHA-256 `fd117eb5f9ac2551ca9fb5f9a7b775e9bcb587cf430c8c9daef71d3169d6ad27`). The final linked image has no unresolved symbols, and decompression of Image.gz exactly matches Image. Kernel test files were not added to Git.

The per-CPU runqueue structure shrank from 2,664 to 2,656 bytes; `task_struct` stayed 2,736 bytes because of layout padding. Do not claim per-task RAM savings from removing the estimator field. Image reduction is not a measured boot/install speedup, and total image bytes are not equivalent to permanent RAM saved.

The raw Image packaged in V2.1 has SHA-256 `2e97c93cd24a83c352ad3e777d98a5eebe0dbe2fad823d8ee77f9ea20d0e3160`; Image.gz-dtb SHA-256 is `fd57e9973a9c44218ec348e474bce9895bf0a8f5b01bc1aef9ddf960d2786e82`. V2.1 uses the raw Image with the original boot ramdisk, separate QCDT and header settings; the gzipped artifact is not flashed directly.

The original linked kernel contains 11,034 dynamic-debug records of 40 bytes each: **441,360 bytes of permanent metadata**, before counting their strings, callsite code or dynamic table allocations. The revised config removes that facility. It keeps `CONFIG_KALLSYMS_ALL`: Qualcomm's common-log driver resolves `log_buf`, `log_buf_len` and `log_first_idx` data symbols for crash logging, so removing all-symbol lookup blindly would lose useful diagnostics.

Scheduler statistics, perf events, general tracing, board drivers and protocols remain for dependency review. CPU/GPU/display clocks, device-tree files, IMS/radio configuration and thermal policy were not edited by this set. The user's 65 Hz display setting is retained. Source comments are absent from the compiled image; removing them would not reduce boot.img.

## Short check after installing V2.1

Keep the original working boot image and ROM ZIP available. The complete V2.1 ZIP includes the correctly packaged replacement boot image; no separate kernel flash is needed.

1. In Balanced, let an app sit, then tap/Home, scroll and switch among a few ordinary apps. Open the camera, lock/unlock and check audio, Wi-Fi, a call and mobile data. This checks E006 scheduling, input response, the preserved device functions and zRAM under ordinary memory pressure.
2. Copy a familiar file to internal storage and the SD card, reopen it and compare its checksum with the original. Save a photo or app document and reopen it. Watch for longer save stalls now that fsync actually completes; do not use forced power loss as a test.
3. Switch Performance → Balanced and collect the profile readbacks described in POWER-PROFILES.md. Check the accepted GPU timer/counter and input pulse in that output. E006 itself should need no setting change.
4. Perform one normal reboot/shutdown and note any new delay, freeze, visual glitch or restart. A short ordinary-use report is sufficient for an initial retention decision; there is no mandatory 20-minute timed run.

One baseline snapshot after those activities can capture clocks, swap and relevant kernel state. If a regression appears, return to the original boot image and identify the first failing area; the independent commits allow a focused follow-up kernel. Do not weaken thermal protection or disable real filesystem sync to hide a regression.
