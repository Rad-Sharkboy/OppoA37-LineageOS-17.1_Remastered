#!/sbin/sh
set -eu
fail() { echo "E016: $*" >&2; exit 1; }
point=/tmp/a37-e016-system
system_block=/dev/block/bootdevice/by-name/system
[ -b "$system_block" ] || fail 'System partition unavailable.'
mounted() {
    while read -r source target rest; do [ "$target" != "$1" ] || return 0; done < /proc/mounts
    return 1
}
for target in /system_root/system /system/system /system /system_root; do
    if mounted "$target"; then umount "$target" || fail "Cannot unmount $target."; fi
done
system_real=$(readlink -f "$system_block")
while read -r source target rest; do
    [ "$(readlink -f "$source" 2>/dev/null || true)" != "$system_real" ] || fail "System still mounted at $target."
done < /proc/mounts
[ ! -L "$point" ] || fail 'Unexpected mount path.'
mkdir -p "$point"
mount -t ext4 -o rw "$system_block" "$point" || fail 'Cannot mount System.'
trap 'umount "$point" >/dev/null 2>&1 || true' EXIT
base=$point/system
[ -d "$base/vendor" ] && [ ! -L "$base/vendor" ] || fail 'Unexpected System layout.'
grep -qx 'ro.a37.remastered.version=2.1-E007' "$base/build.prop" || fail 'Expected installed E007 ROM files.'
while read -r old new path; do
    [ -f "$point/$path" ] && [ ! -L "$point/$path" ] || fail "Missing target: $path"
    actual=$(sha256sum "$point/$path")
    actual=${actual%% *}
    [ "$actual" = "$old" ] || [ "$actual" = "$new" ] || fail "Target changed: $path"
done < /tmp/a37-e016/inputs
overlay=$base/product/overlay
[ -d "$overlay" ] && [ ! -L "$base/product" ] && [ ! -L "$overlay" ] || fail 'Unexpected overlay directory.'
folder=$overlay/A37Brightness
[ ! -L "$folder" ] || fail 'Unexpected overlay folder.'
target=$folder/A37Brightness.apk
[ ! -L "$target" ] || fail 'Unexpected overlay target.'
if [ -e "$target" ]; then
    [ -f "$target" ] || fail 'Overlay target is not a file.'
    expected=$(cat /tmp/a37-e016/overlay.sha256)
    actual=$(sha256sum "$target")
    [ "${actual%% *}" = "$expected" ] || fail 'Existing brightness overlay differs.'
fi
trap - EXIT
