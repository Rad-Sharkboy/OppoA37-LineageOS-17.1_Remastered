#!/system/bin/sh
# One-time boot reconciliation after the old kernel's delayed tuning.
set -eu
profile=${1:-}
case "$profile" in 0|1|2) ;; *) echo 'No verified active Power HAL profile.'; exit 1;; esac
cpu_floor=200000
gpu_floor=200000000
hispeed=998400
timer=80
loads='1 200000:25 400000:35 533333:45 800000:55 998400:65 1094400:65 1152000:70 1209600:80'
if [ "$profile" = 2 ]; then
    hispeed=1209600
    timer=500
    loads='1 200000:25 400000:35 533333:45 800000:55 998400:60 1094400:65 1152000:70 1209600:80'
fi
cpu_applied=0
for cpu in /sys/devices/system/cpu/cpu[0-3]; do
    [ -r "$cpu/cpufreq/scaling_max_freq" ] && [ -w "$cpu/cpufreq/scaling_min_freq" ] || continue
    maximum=$(cat "$cpu/cpufreq/scaling_max_freq")
    [ "$maximum" -gt 0 ] && [ "$maximum" -le 1209600 ] || exit 1
    if [ "$profile" = 2 ] || [ "$cpu_floor" -gt "$maximum" ]; then cpu_floor=$maximum; fi
    printf '%s\n' "$cpu_floor" > "$cpu/cpufreq/scaling_min_freq"
    cpu_applied=1
    break
done
[ "$cpu_applied" = 1 ] || { echo 'No writable online CPU policy.'; exit 1; }
maximum=$(cat /sys/class/kgsl/kgsl-3d0/devfreq/max_freq)
[ "$maximum" -gt 0 ] && [ "$maximum" -le 620000000 ] || exit 1
if [ "$profile" = 2 ] || [ "$gpu_floor" -gt "$maximum" ]; then gpu_floor=$maximum; fi
printf '%s\n' "$gpu_floor" > /sys/class/kgsl/kgsl-3d0/devfreq/min_freq
printf '%s\n' "$hispeed" > /sys/devices/system/cpu/cpufreq/interactive/hispeed_freq
printf '%s\n' "$loads" > /sys/devices/system/cpu/cpufreq/interactive/target_loads
printf '%s\n' "$timer" > /sys/class/kgsl/kgsl-3d0/idle_timer
echo "Reconciled active profile $profile after delayed kernel startup."
