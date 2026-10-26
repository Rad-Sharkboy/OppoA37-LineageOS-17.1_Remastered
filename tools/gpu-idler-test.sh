#!/system/bin/sh
# E004: shorten the GPU idler's NAP deferral, keeping the 80 ms timer.
set -eu
base=/sys/class/kgsl/kgsl-3d0
node=$base/gpu_idler_idleworkload
saved=/data/local/tmp/a37-e004-gpu-idler
mode=${1:-status}
fail() { echo "$*" >&2; exit 1; }
case "$mode" in status|apply|restore) ;; *) fail 'Use: sh gpu-idler-test.sh status|apply|restore';; esac
[ -r "$node" ] || fail 'GPU idle-workload control unavailable; send this output.'
current=$(cat "$node")
echo "GPU idle-workload setting: $current checks (0 uses the kernel fallback of 10)"
for field in gpu_idler idle_timer devfreq/min_freq devfreq/max_freq; do
    if [ -r "$base/$field" ]; then echo "$field=$(cat "$base/$field")"; fi
done
if [ "$mode" = status ]; then exit 0; fi
[ "$(id -u)" = 0 ] && [ -w "$node" ] || fail 'Root and a writable idle-workload node required.'
[ "$(getprop ro.product.device)" = A37 ] || fail 'Expected the confirmed A37 device.'
boot=$(cat /proc/sys/kernel/random/boot_id)
[ ! -L "$saved" ] && [ ! -L "$saved/boot" ] && [ ! -L "$saved/value" ] || fail 'Unexpected saved-state symlink; stop.'
if [ "$mode" = apply ]; then
    up=$(cut -d. -f1 /proc/uptime)
    [ "$up" -ge 300 ] || fail 'Wait five minutes after boot.'
    [ "$(cat "$base/gpu_idler")" = 1 ] || fail 'Expected GPU idler enabled; no change made.'
    [ "$(cat "$base/idle_timer")" = 80 ] || fail 'Keep the accepted GPU timeout at 80 ms first.'
    [ "$(cat "$base/devfreq/min_freq")" = 200000000 ] &&
        [ "$(cat "$base/devfreq/max_freq")" = 620000000 ] || fail 'GPU limits differ from confirmed V2.'
    [ "$(cat /sys/devices/system/cpu/cpufreq/interactive/hispeed_freq)" = 998400 ] || fail 'Keep the accepted CPU initial boost first.'
    if [ -e "$saved" ]; then
        [ -d "$saved" ] && [ -f "$saved/boot" ] && [ -f "$saved/value" ] || fail 'Incomplete saved state; stop.'
        old=$(cat "$saved/value")
        case "$old" in 0|10) ;; *) fail 'Unexpected saved value.';; esac
        if [ "$(cat "$saved/boot")" = "$boot" ]; then
            [ "$current" = 3 ] || fail 'Existing same-boot trial; restore first.'
            echo 'E004 already active.'
            exit 0
        fi
        case "$current" in 0|10) ;; *) fail 'Earlier-boot state and unexpected current value.';; esac
        rm "$saved/boot" "$saved/value"
        rmdir "$saved"
    fi
    case "$current" in 0|10) ;; *) fail 'Expected the original effective threshold of 10; send status.';; esac
    umask 077
    mkdir "$saved"
    printf '%s\n' "$boot" > "$saved/boot"
    printf '%s\n' "$current" > "$saved/value"
    printf '3\n' > "$node"
    [ "$(cat "$node")" = 3 ] || fail 'Readback failed; restore or reboot.'
    echo 'E004 active: 3 idle checks; timer remains 80 ms and clock limits unchanged.'
else
    [ -d "$saved" ] && [ -f "$saved/boot" ] && [ -f "$saved/value" ] || fail 'No complete saved state; reboot restores the installed defaults.'
    [ "$(cat "$saved/boot")" = "$boot" ] || fail 'State belongs to an earlier boot; do not restore it.'
    old=$(cat "$saved/value")
    case "$old" in 0|10) ;; *) fail 'Unexpected saved value.';; esac
    case "$current" in 0|3|10) ;; *) fail 'Another value is active; not overwriting it.';; esac
    # The sysfs setter rejects 0. Explicit 10 restores its fallback behavior.
    printf '10\n' > "$node"
    [ "$(cat "$node")" = 10 ] || fail 'Restore readback failed; reboot.'
    rm "$saved/boot" "$saved/value"
    rmdir "$saved"
    echo 'Restored 10 idle checks; timer, GPU idler enable and clock limits unchanged.'
    if [ "$old" = 0 ]; then echo 'Original raw value 0 meant fallback 10; reboot restores the raw default.'; fi
fi
