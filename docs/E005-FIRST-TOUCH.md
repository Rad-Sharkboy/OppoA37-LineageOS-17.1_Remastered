# E005: prompt first touch and Home-key response

Earlier hardware logs show `input_boost_freq=0:0 1:0 2:0 3:0`: Qualcomm CPU input boosting is disabled. In `drivers/cpufreq/cpu-boost.c`, that causes the input-event handler to return immediately. Both the touchscreen and keypad devices match its input handlers, so this is a plausible contributor to the reported delay before a touch or Home press responds at 200 MHz.

E005 restores only a brief **800 MHz input floor for the existing 40 ms duration**. The kernel removes the floor afterward and can return to 200 MHz. It rate-limits input boosts to once per 150 ms. It does not change the steady minimum, maximum clock, governor table or GPU settings. This consumes some energy per input in exchange for responsiveness; it is not a battery-saving claim.

## Try this before E004

Keep the phone in Balanced and leave the other settings constant. Copy the latest kit's tools folder beside adb.exe:

```bat
.\adb.exe push tools/input-boost-test.sh /data/local/tmp/
.\adb.exe shell "su -c 'sh /data/local/tmp/input-boost-test.sh apply'"
```

Expect `E005 active: 800 MHz for 40 ms after input`. Leave a page still briefly, then tap or press Home; repeat a few times during normal use. Compare the first response with how it behaved before. No long benchmark or constant ADB polling is required.

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/input-boost-test.sh status'"
```

Send whether the delay improved and this short readback. If it does not help, or responsiveness/heat worsens, restore it:

```bat
.\adb.exe shell "su -c 'sh /data/local/tmp/input-boost-test.sh restore'"
```

Reboot also removes this temporary change. Complete this decision before combining it with another new experiment. The profile bridge deliberately leaves input boost alone, so E005 remains independently reversible.
