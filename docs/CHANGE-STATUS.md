# Development changes and final packaging

The final delivery will include a list of changed GitHub files, each exact destination in the ROM kitchen, any required boot.img separately, and repack/rollback steps. Do not copy the whole repository into the ROM.

| Change | Current placement | Integration status |
| --- | --- | --- |
| GPU idle delay 500 → 80 ms | Edited `rom/v2/system/vendor/etc/init/hw/init.qcom.power.rc` | Accepted; preserve at final repack |
| CPU initial boost 1209.6 → 998.4 MHz | Same ROM init file, both Cinnamon kernel startup writes, optional Magisk startup helper for current V2 | Accepted; old V2 kernel can override the ROM file alone |
| Cinnamon I/O latency accounting | `block/cinnamon-iosched.c` in kernel repository | Source fix prepared; needs a rebuilt-kernel device check before inclusion in a release |
| E003 target load at 998.4 MHz: 60% → 65% | Temporary `tools/cpu-target-load-test.sh` | Await ordinary-use feedback; excluded from startup defaults |
| E004 GPU idler threshold: effective 10 → 3 | Temporary `tools/gpu-idler-test.sh` | Prepare after E003 decision; excluded from startup defaults |
| Cinnamon merge compatibility | `block/cinnamon-iosched.c` in kernel repository | Source repair; include in a separately validated replacement kernel |
| Remove duplicate zRAM history comparison | `drivers/block/zram/zcomp_cinnamon.c` in kernel repository | Source optimization; include in a separately validated replacement kernel |

The deeper source findings and later kernel-debloat plan are in KERNEL-DEEP-AUDIT.md.

The kitchen in the supplied screenshot calls the extracted image root `system`. Thus the edited GitHub init file maps to `system/system/vendor/etc/init/hw/init.qcom.power.rc`. This records the mapping, not instructions to repack now. The full replacement list will be generated from the accepted final changes.

The final kernel requires its own build and boot-image packaging, retaining the correct ramdisk, device tree, header and device-specific settings. Current V2 contains a dirty kernel whose changes are not fully represented by the source branch. A successful source build alone is not proof that a replacement boots identically.

Keep the original image metadata for ownership, permissions and SELinux labels when repacking with the kitchen. Diagnostic scripts, development notes, raw logs, original-file inventory and temporary experiment state do not belong in the ROM payload.
