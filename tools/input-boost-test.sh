#!/system/bin/sh
# E005: brief CPU response boost for touchscreen and keypad events.
set -eu
node=/sys/module/cpu_boost/parameters/input_boost_freq
duration=/sys/module/cpu_boost/parameters/input_boost_ms
saved=/data/local/tmp/a37-e005-input-boost
mode=${1:-status}
fail() { echo "$*" >&2; exit 1; }
read_map() { tr -s '[:space:]' ' ' < "$node" | sed 's/^ //;s/ $//'; }
old='0:0 1:0 2:0 3:0'
trial='0:800000 1:800000 2:800000 3:800000'
case "$mode" in status|apply|restore) ;; *) fail 'Use: sh input-boost-test.sh status|apply|restore';; esac
[ -r "$node" ] && [ -r "$duration" ] || fail 'CPU input-boost controls unavailable.'
current=$(read_map)
echo "Input boost: $current"
echo "Duration: $(cat "$duration") ms"
[ "$mode" != status ] || exit 0
[ "$(id -u)" = 0 ] && [ -w "$node" ] || fail 'Root and a writable input-boost node required.'
[ "$(getprop ro.product.device)" = A37 ] || fail 'Expected the confirmed A37 device.'
boot=$(cat /proc/sys/kernel/random/boot_id)
[ ! -L "$saved" ] && [ ! -L "$saved/boot" ] || fail 'Unexpected saved-state symlink.'
if [ "$mode" = apply ]; then
    [ "$(cat "$duration")" = 40 ] || fail 'Expected the existing 40 ms duration; no change made.'
    if [ -e "$saved" ]; then
        [ -d "$saved" ] && [ -f "$saved/boot" ] || fail 'Incomplete saved state.'
        if [ "$(cat "$saved/boot")" = "$boot" ]; then
            [ "$current" = "$trial" ] || fail 'Existing same-boot trial; restore first.'
            echo 'E005 already active.'
            exit 0
        fi
        [ "$current" = "$old" ] || fail 'Old-boot state with unexpected current setting.'
        rm "$saved/boot"
        rmdir "$saved"
    fi
    [ "$current" = "$old" ] || fail 'Input boost is already configured; send status.'
    umask 077
    mkdir "$saved"
    printf '%s\n' "$boot" > "$saved/boot"
    # A scalar safely configures all CPUs, including currently offline ones.
    printf '800000\n' > "$node"
    [ "$(read_map)" = "$trial" ] || fail 'Readback failed; restore or reboot.'
    echo 'E005 active: 800 MHz for 40 ms after input; normal idle minimum unchanged.'
else
    [ -d "$saved" ] && [ -f "$saved/boot" ] || fail 'No saved trial; reboot restores startup settings.'
    [ "$(cat "$saved/boot")" = "$boot" ] || fail 'Saved state is from an earlier boot.'
    case "$current" in "$old"|"$trial") ;; *) fail 'Another input-boost value is active; not overwriting it.';; esac
    printf '0\n' > "$node"
    [ "$(read_map)" = "$old" ] || fail 'Restore readback failed.'
    rm "$saved/boot"
    rmdir "$saved"
    echo 'Restored disabled CPU input boost.'
fi
