#!/system/bin/sh
set -eu
state=/data/system/a37-remastered
marker=$state/e019-setup
[ -f "$marker" ] && exit 0
umask 077
mkdir -p "$state"
if pm path org.a37.overlay.volume.preview >/dev/null 2>&1; then
    cmd overlay list --user 0 com.android.systemui |
        grep -Fqx '[x] org.a37.overlay.volume' &&
        pm uninstall org.a37.overlay.volume.preview >/dev/null 2>&1 || true
fi
pm disable --user 0 org.lineageos.lineageparts/.trust.TrustOnBoardingActivity >/dev/null
pm disable --user 0 org.lineageos.lineageparts/.trust.TrustPreferences >/dev/null
/system/bin/sh /vendor/bin/a37-volume-placement.sh
: > "$marker"
