#!/sbin/sh
set -eu
fail() { echo "Kernel test: $*" >&2; exit 1; }
case "${1:-}" in ''|--check) ;; *) fail 'Unknown installer argument.';; esac
for tool in getprop readlink blockdev sha256sum wc dd sync cmp; do
    command -v "$tool" >/dev/null 2>&1 || fail "Recovery needs $tool."
done
device=$(getprop ro.product.device | tr '[:upper:]' '[:lower:]')
product=$(getprop ro.build.product | tr '[:upper:]' '[:lower:]')
case "$device:$product" in
    a37:*|a37f:*|a37fw:*|*:a37|*:a37f|*:a37fw) ;;
    *) fail 'Expected Oppo A37/A37f/A37fw.';;
esac
boot_block=/dev/block/bootdevice/by-name/boot
[ -b "$boot_block" ] || fail 'Boot partition unavailable.'
capacity=$(blockdev --getsize64 "$boot_block")
image=/tmp/a37-kernel-test/boot.img
expected=$(cat /tmp/a37-kernel-test/boot.sha256)
base=$(cat /tmp/a37-kernel-test/base.sha256)
for value in "$expected" "$base"; do
    case "$value" in ''|*[!0-9a-f]*) fail 'Invalid verification input.';; esac
    [ "${#value}" = 64 ] || fail 'Invalid verification length.'
done
bytes=$(wc -c < "$image")
[ "$bytes" -gt 2048 ] && [ "$((bytes % 2048))" = 0 ] || fail 'Invalid image length.'
[ "$bytes" -le "$capacity" ] || fail 'Boot image exceeds partition.'
actual=$(sha256sum "$image")
[ "${actual%% *}" = "$expected" ] || fail 'Package image differs.'
readback=/tmp/a37-kernel-test/readback.img
trap 'rm -f "$readback"' EXIT
dd if="$boot_block" of="$readback" bs=2048 count="$((bytes / 2048))" || fail 'Cannot read current boot.'
if cmp "$image" "$readback" >/dev/null 2>&1; then
    echo 'Kernel test already installed.'
    exit 0
fi
actual=$(sha256sum "$boot_block")
[ "${actual%% *}" = "$base" ] || fail 'Boot changed since this test was prepared; repackage it to preserve your current Magisk setup.'
[ "${1:-}" != --check ] || exit 0
dd if="$image" of="$boot_block" bs=2048 || fail 'Boot write failed.'
sync || fail 'Boot sync failed.'
dd if="$boot_block" of="$readback" bs=2048 count="$((bytes / 2048))" || fail 'Boot readback failed.'
cmp "$image" "$readback" >/dev/null 2>&1 || fail 'Boot readback differs.'
echo 'Kernel test installed; existing Magisk ramdisk retained.'
