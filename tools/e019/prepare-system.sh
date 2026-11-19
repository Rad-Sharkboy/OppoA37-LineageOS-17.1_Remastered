#!/sbin/sh
set -eu
fail() { echo "E019: $*" >&2; exit 1; }
point=/tmp/a37-e019-system
block=/dev/block/bootdevice/by-name/system
[ -b "$block" ] || fail 'System unavailable.'
mounted() { while read -r source target rest; do [ "$target" != "$1" ] || return 0; done < /proc/mounts; return 1; }
for target in "$point" /system_root/system /system/system /system /system_root; do
    if mounted "$target"; then umount "$target" || fail "Cannot unmount $target"; fi
done
real=$(readlink -f "$block")
while read -r source target rest; do
    [ "$(readlink -f "$source" 2>/dev/null || true)" != "$real" ] || fail "System mounted at $target"
done < /proc/mounts
[ ! -L "$point" ] || fail 'Unexpected mount path.'
mkdir -p "$point"
mount -t ext4 -o rw "$block" "$point" || fail 'Cannot mount System.'
trap 'umount "$point" >/dev/null 2>&1 || true' EXIT
base=$point/system
[ -d "$base/vendor" ] && [ ! -L "$base/vendor" ] || fail 'Unexpected System layout.'
grep -qx 'ro.a37.remastered.version=2.1-E007' "$base/build.prop" || fail 'Unexpected ROM.'
while read -r action old new path uid gid mode label; do
    case "$path" in system/*) ;; *) fail 'Invalid target.';; esac
    case "$path" in *..*) fail 'Invalid path.';; esac
    target=$point/$path
    parent=$target
    while [ "$parent" != "$point" ]; do
        [ ! -L "$parent" ] || fail "Symlink in target: $path"
        parent=${parent%/*}
    done
    case "$action" in
        directory)
            [ ! -e "$target" ] || [ -d "$target" ] || fail "Expected directory: $path"
            continue
            ;;
        write|delete) ;;
        *) fail 'Unknown install action.';;
    esac
    if [ -f "$target" ]; then
        actual=$(sha256sum "$target")
        actual=${actual%% *}
        [ "$actual" = "$old" ] || [ "$actual" = "$new" ] || fail "Changed: $path"
    else
        [ ! -e "$target" ] || fail "Expected file: $path"
        [ "$action" = delete ] || [ "$old" = - ] || fail "Missing: $path"
    fi
done < /tmp/a37-e019/inputs
trap - EXIT
