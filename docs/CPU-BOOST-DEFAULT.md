# Keep the 998.4 MHz initial CPU boost

Interactive now starts its high-load boost at 998.4 MHz instead of jumping straight to 1209.6 MHz. The full 1209.6 MHz maximum remains available when needed. Reducing the initial boost can save some energy during short bursts without a noticeable change in responsiveness.

The user accepted this setting after ordinary use. No further timed comparison is required to retain it. Continue using the phone normally; report any new app-launch delay, scrolling stutter or trouble waking the screen.

## Apply on the installed V2 with Magisk

No TWRP, ROM reinstall or kernel flash is needed. Download the updated `A37-V2-test-kit.zip`, extract it, and put its `tools` folder beside `adb.exe`. Wait at least five minutes after boot, then run these in Windows Command Prompt:

```bat
.\adb.exe push tools/keep-cpu-boost.sh /data/local/tmp/
.\adb.exe shell "su -c 'sh /data/local/tmp/keep-cpu-boost.sh install'"
```

Expect `CPU initial boost: 998400 kHz; maximum unchanged at 1209600 kHz` followed by `Installed`. This applies the value immediately and installs one executable script at `/data/adb/service.d/a37-e002-cpu-hispeed.sh`.

Magisk runs it in its non-blocking late-start stage. The script waits five minutes once, checks the device/governor/frequency limits, writes the target, then exits. It does not remain running or keep forcing a setting. An unusually delayed kernel boot override can still require investigation rather than a polling loop.

At your next normal reboot, wait about six minutes after the home screen appears and check once:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/keep-cpu-boost.sh status'"
```

Expect `Current hispeed: 998400 kHz`. This is just a persistence check, not another timed battery test. If installation or startup reports an error, send that output. Do not run the old E002 experiment's `restore` command after choosing to keep the setting.

This script changes only CPU `hispeed_freq`. The accepted GPU 80 ms setting is retained separately in the edited ROM file described in [GPU-80MS-DEFAULT.md](GPU-80MS-DEFAULT.md); if you have only applied GPU E001 temporarily, reboot can still restore its original 500 ms until that ROM edit is installed. CPU/GPU clock limits, the 65 Hz screen and telephony are untouched by the startup script.

## Roll back

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/keep-cpu-boost.sh remove'"
```

This removes only our CPU startup file and its small last-start log. It also restores original V2 hispeed=1209600 when the existing policy matches. If you have changed kernels/governors, it removes persistence but leaves unexpected live settings alone. A sleeping startup copy checks for removal before applying.

## ROM and kernel sources

The edited `rom/v2/system/vendor/etc/init/hw/init.qcom.power.rc` uses 998400 for the early ROM initialization. Both Cinnamon_Active kernel writes now use 998400 too, including the delayed reapply. They must agree: **the ROM file alone cannot defeat the old installed kernel's later 1209600 write**. Keep the Magisk method with the current V2 kernel; a future kernel built with the source change can supply the setting directly.

The kernel source change does not install a new kernel on the phone. Its original dirty kernel is still the running baseline. For kitchen file replacement, use the same original metadata and path mapping described in V2-BASELINE.md.

Magisk startup reference: https://topjohnwu.github.io/Magisk/guides.html#boot-scripts
