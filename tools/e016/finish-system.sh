#!/sbin/sh
set -eu
point=/tmp/a37-e016-system
trap 'umount "$point" >/dev/null 2>&1 || true' EXIT
target=$point/system/product/overlay/A37Brightness/A37Brightness.apk
[ -f "$target" ] && [ ! -L "$target" ] || exit 1
expected=$(cat /tmp/a37-e016/overlay.sha256)
actual=$(sha256sum "$target")
[ "${actual%% *}" = "$expected" ] || exit 1
sync
umount "$point"
trap - EXIT
