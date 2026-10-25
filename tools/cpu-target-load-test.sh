#!/system/bin/sh
# E003: give only the 998.4 MHz step slightly more load headroom.
set -eu
governor=/sys/devices/system/cpu/cpufreq/interactive
node=$governor/target_loads
gpu=/sys/class/kgsl/kgsl-3d0/idle_timer
saved=/data/local/tmp/a37-e003-cpu-target-load
baseline='1 200000:25 400000:35 533333:45 800000:55 998400:60 1094400:65 1152000:70 1209600:80'
trial='1 200000:25 400000:35 533333:45 800000:55 998400:65 1094400:65 1152000:70 1209600:80'
mode=${1:-status}
fail() { echo "$*" >&2; exit 1; }
case "$mode" in status|apply|restore) ;; *) fail 'Use: sh cpu-target-load-test.sh status|apply|restore';; esac
[ -r "$node" ] || fail 'Interactive target_loads unavailable.'
current=$(cat "$node")
echo "CPU target loads: $current"
if [ -r "$governor/hispeed_freq" ]; then echo "Initial boost: $(cat "$governor/hispeed_freq") kHz"; fi
if [ -r "$gpu" ]; then echo "GPU idle timeout: $(cat "$gpu") ms"; fi
if [ "$mode" = status ]; then
    case "$current" in "$trial") echo 'E003 active: 998.4 MHz target load 65%.';; "$baseline") echo 'E003 baseline: 998.4 MHz target load 60%.';; *) echo 'Different target-load table; do not apply E003.';; esac
    exit 0
fi
[ "$(id -u)" = 0 ] && [ -w "$node" ] || fail 'Root and a writable target-load node required.'
[ "$(getprop ro.product.device)" = A37 ] || fail 'Expected the confirmed A37 device.'
boot=$(cat /proc/sys/kernel/random/boot_id)
[ ! -L "$saved" ] && [ ! -L "$saved/boot" ] && [ ! -L "$saved/value" ] || fail 'Unexpected saved-state symlink; stop.'

if [ "$mode" = apply ]; then
    up=$(cut -d. -f1 /proc/uptime)
    [ "$up" -ge 300 ] || fail 'Wait five minutes after boot.'
    [ "$(cat "$governor/hispeed_freq")" = 998400 ] || fail 'Keep accepted CPU boost 998400 first; see CPU-BOOST-DEFAULT.md.'
    [ -r "$gpu" ] && [ "$(cat "$gpu")" = 80 ] || fail 'Keep the accepted GPU timeout at 80 ms before E003.'
    policy=
    for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
        if [ -r "$cpu/cpufreq/scaling_governor" ]; then policy=$cpu/cpufreq; break; fi
    done
    [ -n "$policy" ] || fail 'No readable online CPU policy.'
    [ "$(cat "$policy/scaling_governor")" = interactive ] || fail 'Expected interactive governor.'
    [ "$(cat "$policy/scaling_min_freq")" = 200000 ] &&
        [ "$(cat "$policy/scaling_max_freq")" = 1209600 ] || fail 'CPU frequency limits differ from the V2 baseline.'
    if [ -e "$saved" ]; then
        [ -d "$saved" ] && [ -f "$saved/boot" ] && [ -f "$saved/value" ] || fail 'Incomplete saved state; stop and report it.'
        [ "$(cat "$saved/value")" = "$baseline" ] || fail 'Unexpected saved table.'
        if [ "$(cat "$saved/boot")" = "$boot" ]; then
            [ "$current" = "$trial" ] || fail 'Existing same-boot experiment; restore it first.'
            echo 'E003 already active; no change made.'
            exit 0
        fi
        [ "$current" = "$baseline" ] || fail 'Earlier-boot state and unexpected live table; stop.'
        rm "$saved/boot" "$saved/value"
        rmdir "$saved"
    fi
    [ "$current" = "$baseline" ] || fail 'Expected the original V2 target-load table; no change made.'
    umask 077
    mkdir "$saved"
    printf '%s\n' "$boot" > "$saved/boot"
    printf '%s\n' "$current" > "$saved/value"
    printf '%s\n' "$trial" > "$node"
    [ "$(cat "$node")" = "$trial" ] || fail 'Readback failed; restore or reboot.'
    echo 'E003 active: 998.4 MHz target load 60% -> 65%; other entries and clocks unchanged.'
else
    [ -d "$saved" ] && [ -f "$saved/boot" ] && [ -f "$saved/value" ] || fail 'No complete saved state; reboot restores the installed startup settings.'
    [ "$(cat "$saved/boot")" = "$boot" ] || fail 'State belongs to an earlier boot; do not restore it.'
    [ "$(cat "$saved/value")" = "$baseline" ] || fail 'Unexpected saved table; stop.'
    case "$current" in "$baseline"|"$trial") ;; *) fail 'Another component changed the table; not overwriting it.';; esac
    printf '%s\n' "$baseline" > "$node"
    [ "$(cat "$node")" = "$baseline" ] || fail 'Restore readback failed; reboot.'
    rm "$saved/boot" "$saved/value"
    rmdir "$saved"
    echo 'Restored 998.4 MHz target load 60%; accepted CPU boost and GPU setting unchanged.'
fi
