#!/sbin/sh
set -eu
fail() { echo "V2.1: $*" >&2; exit 1; }
for tool in getprop readlink blockdev sha256sum wc dd sync cmp; do
    command -v "$tool" >/dev/null 2>&1 || fail "Recovery needs $tool."
done
device=$(getprop ro.product.device | tr '[:upper:]' '[:lower:]')
product=$(getprop ro.build.product | tr '[:upper:]' '[:lower:]')
case "$device:$product" in
    a37:*|a37f:*|a37fw:*|*:a37|*:a37f|*:a37fw) ;;
    *) fail "Expected Oppo A37/A37f/A37fw; recovery reports $device / $product.";;
esac
boot_block=/dev/block/bootdevice/by-name/boot
system_block=/dev/block/bootdevice/by-name/system
[ -b "$boot_block" ] && [ -b "$system_block" ] || fail 'Expected boot/system block devices are unavailable.'
[ "$(readlink -f "$boot_block")" != "$(readlink -f "$system_block")" ] || fail 'Boot and system resolve to the same block device.'
partition_bytes() {
    bytes=$(blockdev --getsize64 "$1") || fail "Cannot read capacity of $1."
    case "$bytes" in ''|*[!0-9]*) fail "Invalid capacity for $1.";; esac
    printf '%s\n' "$bytes"
}
[ "$(partition_bytes "$system_block")" -ge 2859466752 ] || fail 'System partition is smaller than the image.'
[ -f /tmp/boot.img ] && [ -f /tmp/boot.sha256 ] || fail 'Boot image or checksum is missing.'
boot_bytes=$(wc -c < /tmp/boot.img)
[ "$boot_bytes" -gt 2048 ] && [ "$((boot_bytes % 2048))" = 0 ] || fail 'Unexpected boot image length.'
[ "$boot_bytes" -le "$(partition_bytes "$boot_block")" ] || fail 'Boot image exceeds partition capacity.'
boot_hash=$(cat /tmp/boot.sha256)
case "$boot_hash" in ''|*[!0-9a-f]*) fail 'Invalid boot checksum.';; esac
[ "${#boot_hash}" = 64 ] || fail 'Invalid boot checksum length.'
actual=$(sha256sum /tmp/boot.img)
[ "${actual%% *}" = "$boot_hash" ] || fail 'Boot image checksum mismatch.'
mounted() {
    while read -r source target rest; do [ "$target" != "$1" ] || return 0; done < /proc/mounts
    return 1
}
for target in /system_root/system /system/system /system /system_root; do
    if mounted "$target"; then umount "$target" || fail "Cannot unmount $target."; fi
done
system_real=$(readlink -f "$system_block")
while read -r source target rest; do
    [ "$(readlink -f "$source" 2>/dev/null || true)" != "$system_real" ] || fail "System is still mounted at $target."
done < /proc/mounts
sh /tmp/cleanup-tuning.sh
