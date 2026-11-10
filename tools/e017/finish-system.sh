#!/sbin/sh
set -eu
point=/tmp/a37-e017-system
trap 'umount "$point" >/dev/null 2>&1 || true' EXIT
while read -r old new path; do
    target=$point/$path
    [ -f "$target" ] && [ ! -L "$target" ] || exit 1
    actual=$(sha256sum "$target")
    [ "${actual%% *}" = "$new" ] || exit 1
    [ "$(stat -c '%u:%g:%a' "$target")" = '0:0:644' ] || exit 1
    context=$(ls -Zd "$target")
    case "$context" in *u:object_r:system_file:s0*) ;; *) exit 1;; esac
done < /tmp/a37-e017/inputs
sync
umount "$point"
trap - EXIT
