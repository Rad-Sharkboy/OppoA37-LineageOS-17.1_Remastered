#!/sbin/sh
set -eu
point=/tmp/a37-e019-system
trap 'umount "$point" >/dev/null 2>&1 || true' EXIT
fail() { echo "E019: $*" >&2; exit 1; }

# Verify each installed file and its metadata before deleting originals.
while read -r action old new path uid gid mode label; do
    target=$point/$path
    case "$action" in
        delete) continue;;
        directory) [ -d "$target" ] && [ ! -L "$target" ] || fail "Missing directory: $path";;
        write)
            [ -f "$target" ] && [ ! -L "$target" ] || fail "Missing file: $path"
            actual=$(sha256sum "$target")
            [ "${actual%% *}" = "$new" ] || fail "Readback differs: $path"
            ;;
        *) fail 'Unknown install action.';;
    esac
    [ "$(stat -c '%u:%g:%a' "$target")" = "$uid:$gid:$mode" ] || fail "Mode or owner differs: $path"
    context=$(ls -Zd "$target")
    case "$context" in *"$label"*) ;; *) fail "Security label differs: $path";; esac
done < /tmp/a37-e019/inputs

while read -r action old new path uid gid mode label; do
    [ "$action" = delete ] || continue
    target=$point/$path
    [ ! -L "$target" ] || fail "Symlink: $path"
    [ -e "$target" ] || continue
    actual=$(sha256sum "$target")
    [ "${actual%% *}" = "$old" ] || fail "Deletion input differs: $path"
    rm "$target"
    [ ! -e "$target" ] || fail "Could not remove: $path"
done < /tmp/a37-e019/inputs
sync
umount "$point"
trap - EXIT
