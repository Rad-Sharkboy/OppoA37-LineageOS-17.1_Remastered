#!/system/bin/sh
state=/data/system/a37-remastered
marker=$state/e019-volume-left
[ -f "$marker" ] && exit 0
content call --uri content://lineagesettings --method PUT_secure \
    --arg volume_panel_on_left --extra value:s:1 --extra _user:i:0 >/dev/null 2>&1 || exit 1
result=$(content call --uri content://lineagesettings --method GET_secure \
    --arg volume_panel_on_left --extra _user:i:0 2>/dev/null)
case "$result" in *value=1*) ;; *) exit 1 ;; esac
umask 077
mkdir -p "$state" || exit 1
: > "$marker"
