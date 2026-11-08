#!/system/bin/sh
# Read-only snapshot; do not use USB-connected readings as idle-power measurements.
echo 'Oppo A37 E007 snapshot'
date
uname -a
for key in ro.a37.remastered.version ro.lineage.version vendor.a37.profile vendor.a37.profile_apply vendor.a37.boot_apply vendor.a37.cleanup init.svc.vendor.vm_bms gsm.network.type gsm.sim.state; do
    echo "$key=$(getprop "$key")"
done
read_node() { if [ -r "$1" ]; then echo "--- $1"; cat "$1" 2>/dev/null; fi; }
for cpu in /sys/devices/system/cpu/cpu[0-3]; do
    for name in related_cpus scaling_governor scaling_min_freq scaling_max_freq scaling_cur_freq; do read_node "$cpu/cpufreq/$name"; done
done
for name in hispeed_freq target_loads; do read_node /sys/devices/system/cpu/cpufreq/interactive/$name; done
echo 'GPU frequency can retain its last value while clocks are off.'
for name in default_pwrlevel idle_timer gpu_idler_idleworkload gpuclk gpubusy clock_times devfreq/min_freq devfreq/max_freq devfreq/cur_freq; do read_node /sys/class/kgsl/kgsl-3d0/$name; done
for name in input_boost_freq input_boost_ms min_input_interval; do read_node /sys/module/cpu_boost/parameters/$name; done
for supply in battery bms; do
    for name in capacity voltage_now voltage_ocv current_now status present temp charge_counter charge_full cycle_count charging_enabled bypass; do read_node /sys/class/power_supply/$supply/$name; done
done
for name in /dev/vm_bms /system/vendor/bin/vm_bms /vendor/bin/vm_bms; do ls -l "$name" 2>/dev/null; done
for name in /sys/block/mmcblk0/queue/scheduler /sys/block/mmcblk1/queue/scheduler /sys/block/mmcblk0/queue/iosched/read_batch /sys/block/mmcblk0/queue/iosched/batch_stats /sys/block/mmcblk1/queue/iosched/batch_stats /sys/kernel/debug/qpnp_vmbms/bms_status /proc/swaps; do read_node "$name"; done
echo 'End of snapshot. Estimated current/SOC are not calibrated energy measurements.'
exit 0
