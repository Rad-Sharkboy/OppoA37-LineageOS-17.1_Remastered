#!/system/bin/sh
MODDIR=${0%/*}
sh "$MODDIR/post-fs-data.sh"
sleep 300
[ -d "$MODDIR" ] && [ ! -e "$MODDIR/disable" ] && [ ! -e "$MODDIR/remove" ] || exit 0
exec > "$MODDIR/last-boot.log" 2>&1
date
profile=$(getprop vendor.a37.profile)
sh "$MODDIR/apply-profile.sh" "$profile" || exit 1
# If the user switched profiles during these writes, reconcile once more.
current=$(getprop vendor.a37.profile)
if [ "$current" != "$profile" ]; then sh "$MODDIR/apply-profile.sh" "$current"; fi
