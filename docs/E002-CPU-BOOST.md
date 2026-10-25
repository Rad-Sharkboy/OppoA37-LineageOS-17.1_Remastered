# E002: initial CPU boost target 1209.6 → 998.4 MHz

E002 is now accepted for retention after normal use with no noticeable responsiveness loss. Maximum CPU frequency remains 1209.6 MHz. Lowering the initial boost target can reduce energy spent on short bursts while allowing higher frequency when needed.

**To keep the setting, follow [CPU-BOOST-DEFAULT.md](CPU-BOOST-DEFAULT.md).** It takes two ADB commands on the installed V2 with Magisk; no ROM or kernel flash is required. It also explains rollback and the one-time reboot readback check.

The original `cpu-hispeed-test.sh` remains available for temporary comparisons, but its automatic restore step is no longer the instruction for this accepted setting. Do not apply or restore that experiment while the persistent setting is installed.

Hardware observations are recorded in [E002-RESULTS.md](E002-RESULTS.md). Ordinary-use feedback is enough to retain this reversible tuning; longer matched comparisons are optional if a numeric battery estimate is wanted later. The current development priority is drain during normal use.
