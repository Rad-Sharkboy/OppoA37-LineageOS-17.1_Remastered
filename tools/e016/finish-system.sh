#!/sbin/sh
set -eu
point=/tmp/a37-e016-system
trap 'umount "$point" >/dev/null 2>&1 || true' EXIT
target=$point/system/product/overlay/A37Brightness/A37Brightness.apk
folder=$point/system/product/overlay/A37Brightness
[ -f "$target" ] && [ ! -L "$target" ] || exit 1
expected=$(cat /tmp/a37-e016/overlay.sha256)
actual=$(sha256sum "$target")
[ "${actual%% *}" = "$expected" ] || exit 1
[ "$(stat -c '%u:%g:%a' "$folder")" = '0:0:755' ] || exit 1
[ "$(stat -c '%u:%g:%a' "$target")" = '0:0:644' ] || exit 1
for path in "$folder" "$target"; do
    context=$(ls -Zd "$path")
    case "$context" in *u:object_r:vendor_overlay_file:s0*) ;; *) exit 1;; esac
done
sync
umount "$point"
trap - EXIT
