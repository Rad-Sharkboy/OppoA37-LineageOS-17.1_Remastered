#!/sbin/sh
set -eu
[ -d /data/adb ] || exit 0
for path in /data/adb /data/adb/service.d /data/adb/modules /data/adb/a37-v21-backup; do
    [ ! -L "$path" ] || { echo "V2.1: unexpected tuning path symlink: $path" >&2; exit 1; }
done
module=/data/adb/modules/a37_power_profiles
if [ ! -L "$module" ] && [ -f "$module/module.prop" ] && [ ! -L "$module/module.prop" ] &&
   grep -qx 'id=a37_power_profiles' "$module/module.prop" &&
   grep -qx 'version=0.1' "$module/module.prop" &&
   grep -qx 'versionCode=1' "$module/module.prop"; then
    [ ! -L "$module/disable" ] || exit 1
    touch "$module/disable"
fi
old=/data/adb/service.d/a37-e002-cpu-hispeed.sh
if [ -f "$old" ] && [ ! -L "$old" ] &&
   [ "$(sed -n '2p' "$old")" = '# A37 E002 persistent CPU boost v1' ]; then
    umask 077
    mkdir -p /data/adb/a37-v21-backup
    saved=$(mktemp /data/adb/a37-v21-backup/cpu-startup.XXXXXX)
    cp "$old" "$saved"
    chmod 0700 "$saved"
    rm "$old"
fi
