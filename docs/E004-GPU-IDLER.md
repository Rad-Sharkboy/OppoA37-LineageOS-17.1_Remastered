# E004: fewer GPU idle checks before deeper power saving

Finish the E003 decision first, then hold that CPU setting constant during this separate GPU trial. E004 is ready to try afterward; no ROM or kernel flash is needed.

## Source finding

The custom Adreno idler in `drivers/gpu/msm/kgsl_pwrctrl.c:kgsl_idle_check()` can repeatedly defer a transition while the GPU is in NAP with no active users. NAP switches GPU clocks off; SLEEP additionally disables the AXI/bus path and releases the GPU DMA-latency QoS request. SLUMBER stops more of the device.

The idler waits for 10 checks by default. An uninterrupted timer-driven NAP tail with an 80 ms timer can therefore take roughly 800 ms before the deeper transition is allowed. It is **not a guaranteed 800 ms sleep latency**: new activity resets the counter, work scheduling and other idle callbacks affect timing, and a suspend request bypasses this deferral.

E001 shortened each timer interval from 500 to 80 ms. E004 complements it by changing only `gpu_idler_idleworkload` from an effective 10 to 3. The simple uninterrupted-tail example becomes roughly 240 ms, with two deferred timer re-arms instead of nine. GPU clock limits, idler enable, the 80 ms interval, CPU settings and 65 Hz display remain unchanged.

The expected benefit is less time retaining the bus/latency requests and fewer repeated checks between rendering bursts. More frequent deep sleep/wake transitions can instead cost energy or cause stutter; that is the tradeoff to check.

## Check and apply

Use the latest kit's `tools` folder beside `adb.exe`. Keep the accepted GPU timer=80 and CPU boost=998400 active, with at least five minutes uptime.

```bat
.\adb.exe push tools/gpu-idler-test.sh /data/local/tmp/
.\adb.exe shell "su -c 'sh /data/local/tmp/gpu-idler-test.sh status'"
```

Expect GPU idler enabled, timeout 80, and workload 0 or 10. **0 means the kernel's fallback of 10**, not that the idler is disabled. This value was missing from the earlier collector, so the live read is needed. If the node is absent or another value is shown, send the output rather than forcing a change.

After finishing E003:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/gpu-idler-test.sh apply'"
```

Expect `E004 active: 3 idle checks`. Use the phone normally: read a page, pause between scrolls, type, open apps, use the camera preview, and switch the screen off/on. Watch for the first scroll after a pause becoming jerky, delayed wake, rendering glitches or new GPU resets. No timed battery session is required. Send the status output and how it feels; avoid simultaneously changing the CPU table.

## Restore

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/gpu-idler-test.sh restore'"
```

This restores an effective threshold of 10 and leaves the other settings alone. If the original readout was 0, the script writes explicit 10 because the kernel setter rejects 0; both use the same threshold. A reboot restores the original raw default on current V2, while also resetting other temporary experiments. E004 has not been added to startup defaults.
