# Development changes and final packaging

V2.1 packages the accepted ROM tuning, native power-profile integration and rebuilt kernel in one flashable ZIP. Use [V2.1 installation and rollback](V2.1-INSTALL.md); no kitchen file replacement or separate experiment scripts are needed.

| Change | Current placement | Integration status |
| --- | --- | --- |
| GPU idle delay 500 → 80 ms | Edited `rom/v2/system/vendor/etc/init/hw/init.qcom.power.rc` | Included in V2.1; profile-aware |
| CPU initial boost 1209.6 → 998.4 MHz | ROM init, both Cinnamon kernel startup writes and native profile integration | Included in V2.1 |
| Cinnamon I/O latency accounting | `block/cinnamon-iosched.c` in kernel repository | Compiled into the V2.1 combined-test kernel |
| E003 target load at 998.4 MHz: 60% → 65% | Native Power HAL and one-time boot reconciliation | Included in V2.1 for Balanced/Power Save |
| E004 GPU idler threshold: effective 10 → 3 | ROM init and startup helper | Included in V2.1 |
| E005 input response: 800 MHz for 40 ms | ROM init and startup helper | Included in V2.1 |
| Balanced/Performance CPU and GPU policy | Pinned native Power HAL extension, GPU-node permission and boot reconciliation | Integrated in V2.1; profile switching is part of the device check |
| Cinnamon merge compatibility | `block/cinnamon-iosched.c` in kernel repository | Compiled into the V2.1 combined-test kernel |
| Remove duplicate zRAM history comparison | `drivers/block/zram/zcomp_cinnamon.c` in kernel repository | Compiled into the V2.1 combined-test kernel |
| E006 unused estimator work | Scheduler source and schedutil Kconfig dependency | Compiled into the V2.1 combined-test kernel |
| zRAM run history and bounds | Cinnamon compressor/decoder | Compiled into the V2.1 combined-test kernel |
| Dynamic debug and MMC profiling removal | ARM64 A37f defconfig | Compiled into V2.1; normal crash/error logs retained |
| Real filesystem sync completion | `fs/sync.c` and Cinnamon startup source | Compiled into V2.1; removes the bypass and recurring polling. Check save/copy latency |

The deeper source findings and later kernel-debloat plan are in KERNEL-DEEP-AUDIT.md.

All experiment commands ran in Balanced; Performance was selected only for the screenshot. The latest user report confirms E001–E005 applied and working, superseding the earlier refused E004 attempt. V2.1 retains E004's counter and E005's input pulse alongside profile-aware E001/E002/E003.

[E006 kernel work](E006-KERNEL-WORK.md) records the kernel build and local validation. Shipped files stay concise; test scripts and these development notes are not ROM payload.

For future kitchen edits, the supplied screenshot calls the extracted image root `system`: the GitHub init file maps to `system/system/vendor/etc/init/hw/init.qcom.power.rc`. V2.1 already contains the integrated files.

V2.1 packages the rebuilt raw ARM64 Image with the original boot ramdisk, QCDT and header settings. V2 contains a dirty kernel whose changes are not fully represented by the source branch, so the combined device check remains necessary; compilation alone does not establish identical boot behavior.

Keep the original image metadata for ownership, permissions and SELinux labels when repacking with the kitchen. Diagnostic scripts, development notes, raw logs, original-file inventory and temporary experiment state do not belong in the ROM payload.
