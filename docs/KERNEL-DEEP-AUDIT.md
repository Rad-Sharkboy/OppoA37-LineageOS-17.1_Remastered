# Kernel source findings

Focus: active-use battery efficiency, correctness and work reduction while retaining CPU/GPU overclocks, the 65 Hz screen and telephony. Source findings are checked against the configured build and uploaded runtime observations; the installed V2 still contains a different dirty kernel.

## GPU NAP deferral — E004

`drivers/gpu/msm/kgsl_pwrctrl.c` implements the custom idler. `kgsl_idle_check()` increments a counter and re-arms the idle timer while deferring a requested state transition. Its fallback threshold is 10; `kgsl_active_count_get()` resets the count when waking from a non-active state. `_nap()` gates clocks, while `_sleep()` also disables AXI and releases the DMA-latency QoS request; `_slumber()` shuts down further device state.

The user now reports E001–E005 applied and working. The development ROM init retains idle timer=80 and E004 workload threshold=3. See E004-GPU-IDLER.md. The standalone tool remains available for rollback/comparison on the installed V2.

A local state-machine fixture uses the extracted `kgsl_idle_check()` body and confirms nine deferred re-arms at threshold 10 versus two at threshold 3, including raw-0 fallback, active-reference protection and suspend bypass. It models state control rather than physical GPU power or timing. The phone script separately passed apply/readback/restore and baseline-guard fixtures, including restoring effective 10 after a raw-0 default.

## Cinnamon I/O merge compatibility

`block/cinnamon-iosched.c:cinnamon_merge()` formerly selected a request solely from sector adjacency. Its CRITICAL queue can contain both reads and writes, and the write search considers the TRIM queue. `block/elevator.c:elv_merge()` checks cached/hash candidates but trusts the scheduler callback. The downstream segment checks do not replace the missing `elv_rq_merge_ok()` check.

The fix invokes that existing compatibility helper before returning either front or back merge. It retains the eight-candidate scan bound, queue ordering and write durability. This is a correctness repair, not a claimed battery or throughput gain.

The local regression compiles extracted scheduler and block compatibility functions with host fixtures. The original implementation fails the incompatible-operation cases; the fixed version accepts valid front/back merges and rejects mismatched direction, discard/secure/write-same flags, device, integrity, encryption, special requests and non-mergeable requests. The eight-candidate limit is also covered. The ARM64 GCC 4.9 scheduler object compiles.

When testing a replacement kernel later, exercise app use during internal/SD file copies, compare copied-file hashes and check storage errors. The original boot image is the rollback. No filesystem reformat or destructive storage test is needed.

## Remove repeated zRAM block comparisons

Both `cinnamon_compress_neon_batched()` and the generic path in `drivers/block/zram/zcomp_cinnamon.c` first compare the current block with the newest history block, then repeat the failed comparison at the start of their four-block search. Skipping that already-rejected entry removes redundant work. The first page block still searches all four entries; successful quick matches keep the same path, encoding and history updates.

The configured ARM64 build enables Cinnamon compression and the NEON path. The later CPU-B snapshot shows approximately 6.2 MiB of swap in use, with nonzero swap-in/out counters; this path is relevant when memory is reclaimed, rather than continuously throughout phone use.

Local before/after checks exercised 6,000 pages at 16/32/64-byte block sizes across generic and batched compressor control flow, with decompression round trips and undefined-behavior checks. Compressed bytes were identical. Instrumented exact-match calls fell from 2,416,000 to 1,970,800 in that corpus. This is a comparison count, not a measured CPU-time or energy percentage. On the x86 host, the NEON primitives used equivalent generic stand-ins; the actual ARM64 assembly was compiled in the kernel object, not executed. Device validation should include normal app switching with swap use and checking for compression/decompression errors.

## Kernel debloat after battery tuning

Start with a dependency map against the active device tree and drivers actually used. Candidates include scheduler statistics, profiling/trace facilities, oversized symbol metadata, unrelated board drivers and unused protocols. For each removal, measure linked image/section sizes and runtime allocations, then preserve the diagnostic or device functionality that is still needed. `CONFIG_SCHEDSTATS`, `CONFIG_PROFILING`, `CONFIG_PERF_EVENTS`, `CONFIG_KALLSYMS_ALL` and tracing are enabled in the prepared config; their presence is an audit lead, not permission to disable all of them together.

Smaller inactive code reduces image/static memory costs, while eliminating executed bookkeeping or work queues can reduce CPU work. Boot/install time must be measured separately. Keep the current build as a comparison and use one configuration change per commit. Do not trim modem/IMS, storage, filesystem, display or rollback support merely to make the file smaller.

The audit also checked scheduler granularity, HRTICK, charger logging and recurring Cinnamon work. HRTICK is compiled but disabled as a scheduler feature by default; large charger status logs are already compiled out; the main interactive/Cinnamon I/O paths do not have routine printk overhead. Those are not current removal wins.

The subsequent E006 audit found unused UTIL_EST updates, dynamic debug metadata, MMC profiling checks, redundant zRAM run-history writes and missing decoder bounds. It also traced the recurring Cinnamon fsync worker to a bypass that skipped real filesystem sync calls. These changes and validation are recorded in [E006-KERNEL-WORK.md](E006-KERNEL-WORK.md). KALLSYMS_ALL is retained because Qualcomm's common-log driver resolves data symbols through it for crash logging.
