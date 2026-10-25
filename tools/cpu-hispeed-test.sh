#!/system/bin/sh
# E002 changes only interactive's initial boost target, not maximum clocks.
set -eu
node=/sys/devices/system/cpu/cpufreq/interactive/hispeed_freq
gpu=/sys/class/kgsl/kgsl-3d0/idle_timer
saved=/data/local/tmp/a37-e002-cpu-hispeed
mode=${1:-status}
case "$mode" in status|apply|restore) ;; *) echo 'Use: sh cpu-hispeed-test.sh status|apply|restore' >&2; exit 2;; esac
[ -r "$node" ] || { echo 'Interactive hispeed node unavailable; collect baseline.' >&2; exit 1; }
current=$(cat "$node")
echo "CPU initial boost target: $current kHz"
[ "$mode" != status ] || exit 0
[ "$(id -u)" = 0 ] && [ -w "$node" ] || { echo 'Root and writable hispeed node required.' >&2; exit 1; }
boot=$(cat /proc/sys/kernel/random/boot_id)
if [ "$mode" = apply ]; then
    [ "$(getprop ro.product.device)" = A37 ] || { echo 'Expected the confirmed A37 device.' >&2; exit 1; }
    up=$(cut -d. -f1 /proc/uptime)
    [ "$up" -ge 300 ] || { echo 'Wait five minutes after boot.' >&2; exit 1; }
    [ "$current" = 1209600 ] || { echo 'Expected baseline hispeed 1209600; no change made.' >&2; exit 1; }
    [ -r "$gpu" ] && [ "$(cat "$gpu")" = 80 ] || { echo 'Keep accepted GPU timeout at 80 ms for both CPU test sessions.' >&2; exit 1; }
    policy=
    for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
        if [ -r "$cpu/cpufreq/scaling_governor" ]; then policy=$cpu/cpufreq; break; fi
    done
    [ -n "$policy" ] || { echo 'No readable online CPU policy.' >&2; exit 1; }
    [ "$(cat "$policy/scaling_governor")" = interactive ] || { echo 'Expected interactive governor.' >&2; exit 1; }
    [ "$(cat "$policy/scaling_max_freq")" = 1209600 ] || { echo 'Maximum frequency differs from confirmed baseline; stop.' >&2; exit 1; }
    frequencies=" $(cat "$policy/scaling_available_frequencies") "
    case "$frequencies" in *' 998400 '*) ;; *) echo '998400 kHz unavailable.' >&2; exit 1;; esac
    [ ! -e "$saved" ] && [ ! -L "$saved" ] || { echo "Existing $saved; restore first or remove stale state after reboot." >&2; exit 1; }
    umask 077
    mkdir "$saved"
    printf '%s\n' "$boot" > "$saved/boot"
    printf '%s\n' "$current" > "$saved/value"
    printf '998400\n' > "$node"
    [ "$(cat "$node")" = 998400 ] || { echo 'Readback failed; restore or reboot.' >&2; exit 1; }
    echo 'E002 active: initial boost target 998400 kHz. Maximum clocks were not changed.'
else
    [ ! -L "$saved" ] && [ -d "$saved" ] || { echo 'No saved state; reboot restores startup settings.' >&2; exit 1; }
    [ "$(cat "$saved/boot")" = "$boot" ] || { echo 'State belongs to an earlier boot; do not restore it.' >&2; exit 1; }
    old=$(cat "$saved/value")
    [ "$old" = 1209600 ] || { echo 'Unexpected saved value; stop.' >&2; exit 1; }
    printf '%s\n' "$old" > "$node"
    [ "$(cat "$node")" = "$old" ] || { echo 'Restore failed; reboot.' >&2; exit 1; }
    rm "$saved/boot" "$saved/value"
    rmdir "$saved"
    echo 'Restored CPU initial boost target 1209600 kHz.'
fi
