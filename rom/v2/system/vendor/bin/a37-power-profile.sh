#!/system/bin/sh
[ "$(getprop ro.a37.remastered.version)" = 2.1 ] || exit 1
cleanup_tuning() (
set -eu
[ -d /data/adb ] || exit 0
for path in /data/adb /data/adb/service.d /data/adb/modules /data/adb/a37-v21-backup; do
    [ ! -L "$path" ] || { echo "V2.1: unexpected tuning path symlink: $path" >&2; exit 1; }
done
module=/data/adb/modules/a37_power_profiles
if [ ! -L "$module" ] && [ -f "$module/module.prop" ] && [ ! -L "$module/module.prop" ] &&
   grep -qx 'id=a37_power_profiles' "$module/module.prop" &&
   grep -qx 'version=0.1' "$module/module.prop" &&
   grep -qx 'versionCode=1' "$module/module.prop"; then
    [ ! -L "$module/disable" ] || exit 1
    touch "$module/disable"
fi
old=/data/adb/service.d/a37-e002-cpu-hispeed.sh
if [ -f "$old" ] && [ ! -L "$old" ] &&
   [ "$(sed -n '2p' "$old")" = '# A37 E002 persistent CPU boost v1' ]; then
    umask 077
    mkdir -p /data/adb/a37-v21-backup
    saved=$(mktemp /data/adb/a37-v21-backup/cpu-startup.XXXXXX)
    cp "$old" "$saved"
    chmod 0700 "$saved"
    rm "$old"
fi
)
apply_profile() (
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
)
initialize_tuning() (
set -eu
chown 1000:1000 /sys/class/kgsl/kgsl-3d0/devfreq/min_freq
chmod 0664 /sys/class/kgsl/kgsl-3d0/devfreq/min_freq
echo 3 > /sys/class/kgsl/kgsl-3d0/gpu_idler_idleworkload
echo 40 > /sys/module/cpu_boost/parameters/input_boost_ms
echo 800000 > /sys/module/cpu_boost/parameters/input_boost_freq
)
incomplete() { setprop vendor.a37.boot_apply incomplete; exit 1; }
cleanup_tuning
[ "$?" = 0 ] || { setprop vendor.a37.cleanup incomplete; incomplete; }
initialize_tuning
[ "$?" = 0 ] || incomplete
sleep 300 || incomplete
profile=$(getprop vendor.a37.profile)
apply_profile "$profile"
[ "$?" = 0 ] || incomplete
current=$(getprop vendor.a37.profile)
if [ "$current" != "$profile" ]; then
    apply_profile "$current"
    [ "$?" = 0 ] || incomplete
fi
setprop vendor.a37.boot_apply ok
