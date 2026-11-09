# E015 sensor/storage cleanup

Install over E014. Boot-only update; retains the installed Magisk ramdisk and device tree.

- Rotation sensor: turn power back off if activation fails.
- Light/proximity: avoid powering up an already-off chip for redundant disable requests; stop light polling before removing power; unwind failed initialization.
- Storage: release the CPU latency request after an immediately rejected request, skip empty release timers, and finish queued release work before removing the host.

1. TWRP → **Install** → `Download/E015-update.zip` → swipe. **No Data wipe.**
2. Reboot. Kernel version should contain `E015-gc3956446`.
3. Check auto-rotation, auto brightness through several screen-off/on cycles, and screen-off/return when moving the phone to/from your ear during a normal call.
4. Try camera/video and scrolling while copying/opening a file. Reconnect USB afterward for verification.

Fallback: TWRP → **Install Image** → `Download/E014-boot.img` → **Boot**.

CPU/GPU undervolts and limits, 65Hz, thermal protection, camera fixes, USB workaround and Data cache/barriers retain E014 settings. GPU200MHz behaviour and Power Save tuning remain deferred.

Validation: three ARM64 drivers compiled; 214 UBSan fault-fixture checks passed, with original failures reproduced. Complete kernel/package validation is recorded in the build manifest. Hardware error paths were simulated; battery gains are unmeasured.
