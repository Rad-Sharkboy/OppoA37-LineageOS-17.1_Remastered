#!/system/bin/sh
# A37 E002 persistent CPU boost v1
# Retain 998.4 MHz initial boost; leave maximum CPU frequency unchanged.
set -eu
node=/sys/devices/system/cpu/cpufreq/interactive/hispeed_freq
directory=/data/adb/service.d
installed=$directory/a37-e002-cpu-hispeed.sh
result=/data/adb/a37-e002-cpu-hispeed.log
mode=${1:-boot}

fail() { echo "$*" >&2; exit 1; }
owned() {
    [ -f "$installed" ] && [ ! -L "$installed" ] &&
        [ "$(sed -n '2p' "$installed")" = '# A37 E002 persistent CPU boost v1' ]
}
validate() {
    [ "$(getprop ro.product.device)" = A37 ] || fail 'Expected the confirmed A37 device.'
    up=$(cut -d. -f1 /proc/uptime)
    [ "$up" -ge 300 ] || fail 'Wait five minutes after boot, then retry.'
    [ -w "$node" ] || fail 'Interactive hispeed node unavailable or not writable.'
    current=$(cat "$node")
    case "$current" in 1209600|998400) ;; *) fail "Unexpected hispeed $current; no tuning applied.";; esac
    policy=
    for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
        if [ -r "$cpu/cpufreq/scaling_governor" ]; then policy=$cpu/cpufreq; break; fi
    done
    [ -n "$policy" ] || fail 'No readable online CPU policy.'
    [ "$(cat "$policy/scaling_governor")" = interactive ] || fail 'Expected interactive governor.'
    [ "$(cat "$policy/scaling_max_freq")" = 1209600 ] || fail 'Maximum frequency differs from V2.'
    frequencies=" $(cat "$policy/scaling_available_frequencies") "
    case "$frequencies" in *' 998400 '*) ;; *) fail '998400 kHz unavailable.';; esac
}
apply() {
    validate
    printf '998400\n' > "$node"
    [ "$(cat "$node")" = 998400 ] || fail 'Hispeed readback failed.'
    echo 'CPU initial boost: 998400 kHz; maximum unchanged at 1209600 kHz.'
}

case "$mode" in boot|install|status|remove) ;; *) fail 'Use: sh keep-cpu-boost.sh install|status|remove';; esac
[ "$(id -u)" = 0 ] || fail 'Root required.'
[ ! -L "$directory" ] && [ ! -L "$installed" ] && [ ! -L "$result" ] || fail 'Unexpected symlink; stop.'

case "$mode" in
    status)
        if owned; then echo 'CPU startup setting installed.'; else echo 'CPU startup setting not installed by this tool.'; fi
        if [ -r "$node" ]; then echo "Current hispeed: $(cat "$node") kHz"; else echo 'Hispeed node unavailable.'; fi
        if [ -f "$result" ]; then echo 'Last startup result:'; cat "$result"; fi
        ;;
    install)
        command -v magisk >/dev/null 2>&1 && magisk -v >/dev/null 2>&1 || fail 'Magisk required for this startup method.'
        [ -d /data/adb ] || fail 'Magisk data directory unavailable.'
        validate
        if [ -e "$installed" ]; then owned || fail 'An unrelated startup file exists; not replacing it.'; fi
        umask 077
        mkdir -p "$directory"
        temporary=$(mktemp /data/adb/a37-e002-install.XXXXXX)
        trap 'rm -f "$temporary"' EXIT
        cp "$0" "$temporary"
        chown 0:0 "$temporary"
        chmod 0700 "$temporary"
        mv -f "$temporary" "$installed"
        trap - EXIT
        apply
        echo 'Installed. Magisk will apply this once, about five minutes after each boot.'
        ;;
    boot)
        # Late-start service is non-blocking. Wait once for Cinnamon's boot writes.
        owned || exit 0
        sleep 300
        # Removal during the wait must cancel this pending write too.
        owned || exit 0
        [ ! -L "$result" ] || exit 1
        umask 077
        exec > "$result" 2>&1
        date
        apply
        ;;
    remove)
        if [ -e "$installed" ]; then
            owned || fail 'Unrecognized startup file; not removing it.'
            rm "$installed"
        fi
        rm -f "$result"
        echo 'CPU startup setting removed.'
        # Delete persistence even if a new kernel/governor prevents safe rollback.
        if (validate); then
            printf '1209600\n' > "$node"
            [ "$(cat "$node")" = 1209600 ] || fail 'Restore readback failed.'
            echo 'Restored original V2 hispeed 1209600 kHz.'
        else
            echo 'Current tuning left alone; reboot restores your installed ROM/kernel defaults.'
        fi
        ;;
esac
