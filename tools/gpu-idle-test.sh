#!/system/bin/sh
# E001: change only the GPU's idle timeout, preserving frequency/voltage tables.
set -eu
node=/sys/class/kgsl/kgsl-3d0/idle_timer
saved=/data/local/tmp/a37-e001-gpu-idle
mode=${1:-status}
case "$mode" in status|apply|restore) ;; *) echo 'Use: sh gpu-idle-test.sh status|apply|restore' >&2; exit 2;; esac
[ -r "$node" ] || { echo "Missing readable $node; stop and report baseline." >&2; exit 1; }
current=$(cat "$node")
echo "GPU idle timeout: $current ms"
[ "$mode" != status ] || exit 0
[ "$(id -u)" = 0 ] && [ -w "$node" ] || { echo 'Root and a writable idle_timer are required.' >&2; exit 1; }
boot=$(cat /proc/sys/kernel/random/boot_id)
if [ "$mode" = apply ]; then
    up=$(cut -d. -f1 /proc/uptime)
    [ "$up" -ge 300 ] || { echo 'Wait at least 5 minutes after boot before testing.' >&2; exit 1; }
    [ "$current" = 500 ] || { echo 'Expected baseline 500 ms. No change made; report the current value.' >&2; exit 1; }
    [ ! -e "$saved" ] && [ ! -L "$saved" ] || { echo "Existing $saved: restore first, or remove stale state after reboot." >&2; exit 1; }
    umask 077
    mkdir "$saved"
    printf '%s\n' "$boot" > "$saved/boot"
    printf '%s\n' "$current" > "$saved/value"
    printf '80\n' > "$node"
    [ "$(cat "$node")" = 80 ] || { echo 'Readback failed; restore or reboot.' >&2; exit 1; }
    echo 'E001 active: 80 ms. Reboot or run restore to revert. No boot file changed.'
else
    [ ! -L "$saved" ] && [ -d "$saved" ] || { echo 'No saved state; reboot restores the normal boot configuration.' >&2; exit 1; }
    [ "$(cat "$saved/boot")" = "$boot" ] || { echo 'Saved state is from another boot; do not restore it. Normal boot settings already apply.' >&2; exit 1; }
    old=$(cat "$saved/value")
    [ "$old" = 500 ] || { echo 'Unexpected saved value; stop.' >&2; exit 1; }
    printf '%s\n' "$old" > "$node"
    [ "$(cat "$node")" = "$old" ] || { echo 'Restore readback failed; reboot.' >&2; exit 1; }
    rm "$saved/boot" "$saved/value"
    rmdir "$saved"
    echo 'Restored 500 ms.'
fi
