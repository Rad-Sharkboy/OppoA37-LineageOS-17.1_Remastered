# Retain the accepted 80 ms GPU timeout

The user accepted E001 for retention after observing no noticeable slowdown. Lower idle-tail overhead is plausible; no numeric battery saving has been measured. CPU/GPU frequency limits and the working 65 Hz display setting remain unchanged.

The custom GPU idler can defer deeper sleep for multiple timer expiries while the GPU is in NAP. Thus 80 ms is the idle timer interval, not a promise of full GPU sleep after 80 ms. E004-GPU-IDLER.md explains the additional counter and a separate trial to reduce it.

`rom/v2/system/vendor/etc/init/hw/init.qcom.power.rc` now adds one write in the existing `enable-low-power` action:

```rc
write /sys/class/kgsl/kgsl-3d0/idle_timer 80
```

## Install with the ROM kitchen

Download the edited file and replace the kitchen's `system/system/vendor/etc/init/hw/init.qcom.power.rc` (the first `system` is the extracted image root shown in the user's screenshot). Preserve the original file metadata using the same kitchen/repack workflow. This file is not flashable by itself. There is no need to rebuild or flash a kernel for this ROM-setting change.

Saving this file on GitHub does not change the current phone. Until the edited ROM is installed, the existing `gpu-idle-test.sh apply` command remains a temporary way to use 80 ms; a normal reboot may restore 500 ms.

After installing the edited ROM, wait five minutes after boot and run:

```bat
.\adb.exe shell su -c "cat /sys/class/kgsl/kgsl-3d0/idle_timer"
```

Expect 80; repeat after screen-off/on. Verify brightness, 65 Hz smoothness and GPU frequency limits behave as before. If another component overrides it, collect the baseline rather than adding a repeated polling loop.

Rollback the ROM change by removing just the added write/comment or restoring the prior version of this file, then repack with the same metadata. A temporary runtime rollback is `adb shell su -c 'echo 500 > /sys/class/kgsl/kgsl-3d0/idle_timer'`; after installing this persistent change, reboot will apply 80 again.

For later CPU/I/O experiments, keep GPU timeout at 80 in both control and experiment sessions. The older E001 restore-after-test advice describes the original exploratory phase; the user's current preference is to retain 80.
