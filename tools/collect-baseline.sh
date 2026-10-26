#!/system/bin/sh
# Read-only, one-shot snapshot. Run before and after a workload, not in a loop.
read_node() {
    [ -f "$1" ] && [ -r "$1" ] || return 0
    printf '\n--- %s ---\n' "$1"
    cat "$1" 2>&1
}
printf 'A37 battery study snapshot v1\n'
date -u
id
uname -a
for prop in ro.product.model ro.product.device ro.build.fingerprint sys.boot_completed dev.bootcomplete vendor.post_boot.parsed; do
    printf '%s=' "$prop"
    getprop "$prop"
done
for node in /proc/uptime /proc/meminfo /proc/vmstat /proc/stat /proc/wakelocks /sys/kernel/debug/wakeup_sources /proc/wakelock_blocker /sys/module/lpm_levels/parameters/sleep_disabled /sys/devices/system/cpu/online /sys/module/cpu_boost/parameters/input_boost_freq /sys/module/cpu_boost/parameters/input_boost_ms; do
    read_node "$node"
done
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
    for field in scaling_governor scaling_min_freq scaling_max_freq scaling_cur_freq scaling_available_frequencies stats/time_in_state; do
        read_node "$cpu/cpufreq/$field"
    done
    for state in "$cpu"/cpuidle/state*; do
        for field in name desc disable usage time; do read_node "$state/$field"; done
    done
done
for gov in /sys/devices/system/cpu/cpufreq/interactive /sys/devices/system/cpu/cpu0/cpufreq/interactive; do
    for field in hispeed_freq go_hispeed_load target_loads timer_rate timer_slack min_sample_time above_hispeed_delay io_is_busy boost boostpulse_duration; do
        read_node "$gov/$field"
    done
done
for field in idle_timer gpuclk gpu_available_frequencies gpubusy gpu_idler gpu_idler_idleworkload force_clk_on force_bus_on force_rail_on devfreq/cur_freq devfreq/min_freq devfreq/max_freq devfreq/available_frequencies devfreq/trans_stat; do
    read_node "/sys/class/kgsl/kgsl-3d0/$field"
done
for supply in battery bms usb ac; do
    for field in status capacity voltage_now current_now charge_counter charge_full temp online bypass; do
        read_node "/sys/class/power_supply/$supply/$field"
    done
done
for zone in /sys/class/thermal/thermal_zone*; do
    read_node "$zone/type"
    read_node "$zone/temp"
done
printf '\n--- Android battery (read-only; current/SOC may be estimated) ---\n'
dumpsys battery
printf '\n--- Android power ---\n'
dumpsys power
if [ -n "${1:-}" ]; then
    printf '\n--- Frame timings: %s ---\n' "$1"
    dumpsys gfxinfo "$1" framestats
fi
