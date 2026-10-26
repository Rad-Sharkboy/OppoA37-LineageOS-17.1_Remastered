# Development changes and final packaging

The final delivery will include a list of changed GitHub files, each exact destination in the ROM kitchen, any required boot.img separately, and repack/rollback steps. Do not copy the whole repository into the ROM.

| Change | Current placement | Integration status |
| --- | --- | --- |
| GPU idle delay 500 → 80 ms | Edited `rom/v2/system/vendor/etc/init/hw/init.qcom.power.rc` | Accepted; preserve at final repack |
| CPU initial boost 1209.6 → 998.4 MHz | Same ROM init file, both Cinnamon kernel startup writes, optional Magisk startup helper for current V2 | Accepted; old V2 kernel can override the ROM file alone |
| Cinnamon I/O latency accounting | `block/cinnamon-iosched.c` in kernel repository | Source fix prepared; needs a rebuilt-kernel device check before inclusion in a release |
| E003 target load at 998.4 MHz: 60% → 65% | Standalone trial and optional profile module | Accepted for retention; profile module applies it in Balanced/Power Save |
| E004 GPU idler threshold: effective 10 → 3 | Temporary `tools/gpu-idler-test.sh` | Last attempt refused at GPU timeout=500 ms; not applied or retained |
| E005 input response: 800 MHz for 40 ms | Temporary `tools/input-boost-test.sh` | Prepared for the reported first-touch/Home delay; awaiting feedback |
| Balanced/Performance CPU and GPU policy | `tools/power-profile-bridge` builds a pinned native Power HAL extension and reversible Magisk overlay | Ready for profile-switch device check; final kitchen payload must include HAL, narrow GPU-node permission and boot reconciliation together |
| Cinnamon merge compatibility | `block/cinnamon-iosched.c` in kernel repository | Source repair; include in a separately validated replacement kernel |
| Remove duplicate zRAM history comparison | `drivers/block/zram/zcomp_cinnamon.c` in kernel repository | Source optimization; include in a separately validated replacement kernel |

The deeper source findings and later kernel-debloat plan are in KERNEL-DEEP-AUDIT.md.

The user clarified that all experiment commands ran in Balanced; Performance was selected only for the screenshot. The pasted E003 output showed the original target-load entry and CPU/GPU values despite the reported no-slowdown result. Retain the requested E003 policy, and use the new profile status readback to establish the installed values. The profile module leaves E004's counter and E005's input pulse untouched.

The kitchen in the supplied screenshot calls the extracted image root `system`. Thus the edited GitHub init file maps to `system/system/vendor/etc/init/hw/init.qcom.power.rc`. This records the mapping, not instructions to repack now. The full replacement list will be generated from the accepted final changes.

The final kernel requires its own build and boot-image packaging, retaining the correct ramdisk, device tree, header and device-specific settings. Current V2 contains a dirty kernel whose changes are not fully represented by the source branch. A successful source build alone is not proof that a replacement boots identically.

Keep the original image metadata for ownership, permissions and SELinux labels when repacking with the kitchen. Diagnostic scripts, development notes, raw logs, original-file inventory and temporary experiment state do not belong in the ROM payload.
