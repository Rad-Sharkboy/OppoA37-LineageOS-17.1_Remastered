#!/system/bin/sh
MODDIR=${0%/*}
old=/data/adb/service.d/a37-e002-cpu-hispeed.sh
if [ -f "$MODDIR/previous-cpu-startup.sh" ] && [ ! -e "$old" ] && [ ! -L "$old" ]; then
    mkdir -p /data/adb/service.d
    cp "$MODDIR/previous-cpu-startup.sh" "$old"
    chmod 0700 "$old"
fi
