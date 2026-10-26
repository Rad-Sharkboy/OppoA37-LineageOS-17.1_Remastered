#!/system/bin/sh
# Reversible Magisk overlay for the exact original A37 V2 Power HAL.
set -eu
source_dir=${0%/*}
module=/data/adb/modules/a37_power_profiles
original=/vendor/bin/hw/android.hardware.power@1.2-service-qti
old_cpu=/data/adb/service.d/a37-e002-cpu-hispeed.sh
mode=${1:-status}
fail() { echo "$*" >&2; exit 1; }
owned() { [ -f "$module/module.prop" ] && grep -qx 'id=a37_power_profiles' "$module/module.prop"; }
case "$mode" in install|status|remove) ;; *) fail 'Use: sh install.sh install|status|remove';; esac
[ "$(id -u)" = 0 ] || fail 'Root required.'
[ ! -L "$module" ] && [ ! -L /data/adb/modules ] && [ ! -L /data/adb/service.d ] && [ ! -L "$old_cpu" ] || fail 'Unexpected installation symlink; stop.'
case "$mode" in
    status)
        if owned; then
            echo 'Profile bridge installed.'
            if [ -e "$module/disable" ] || [ -e "$module/remove" ]; then echo 'Disabled/removing at next reboot.'; fi
        else echo 'Profile bridge not installed.'; fi
        echo "Active HAL profile: $(getprop vendor.a37.profile) (0=Power Save, 1=Balanced, 2=Performance)"
        echo "Last HAL write result: $(getprop vendor.a37.profile_apply)"
        echo 'Saved Lineage profile preference:'
        content query --uri content://lineagesettings/secure --projection name:value --where "name='performance_profile'" 2>/dev/null || true
        for cpu in /sys/devices/system/cpu/cpu[0-3]; do
            [ -r "$cpu/cpufreq/scaling_min_freq" ] || continue
            echo "$cpu minimum=$(cat "$cpu/cpufreq/scaling_min_freq") maximum=$(cat "$cpu/cpufreq/scaling_max_freq")"
            break
        done
        for node in /sys/devices/system/cpu/cpufreq/interactive/hispeed_freq /sys/devices/system/cpu/cpufreq/interactive/target_loads /sys/class/kgsl/kgsl-3d0/devfreq/min_freq /sys/class/kgsl/kgsl-3d0/devfreq/max_freq /sys/class/kgsl/kgsl-3d0/idle_timer /sys/class/kgsl/kgsl-3d0/gpu_idler_idleworkload /sys/module/cpu_boost/parameters/input_boost_freq /sys/module/cpu_boost/parameters/input_boost_ms; do
            if [ -r "$node" ]; then echo "$node=$(cat "$node")"; fi
        done
        if [ -f "$module/last-boot.log" ]; then echo 'Boot reconciliation:'; cat "$module/last-boot.log"; fi
        ;;
    install)
        [ "$(getprop ro.product.device)" = A37 ] || fail 'Expected the confirmed A37 device.'
        command -v magisk >/dev/null 2>&1 && magisk -v >/dev/null 2>&1 || fail 'Magisk required.'
        [ -d /data/adb/modules ] || fail 'Magisk modules directory unavailable.'
        [ ! -e "$module" ] || fail 'Module already exists. Use status; remove and reboot before replacing it.'
        if [ -e "$old_cpu" ]; then
            [ "$(sed -n '2p' "$old_cpu")" = '# A37 E002 persistent CPU boost v1' ] || fail 'Unknown older CPU startup helper; not moving it.'
        fi
        . "$source_dir/payload.sh"
        [ "$(sha256sum "$original" | cut -d' ' -f1)" = "$A37_ORIGINAL_SHA256" ] || fail 'Power HAL differs from pinned V2; no changes made.'
        umask 077
        stage=$(mktemp -d /data/adb/a37-profile-stage.XXXXXX)
        trap 'rm -rf "$stage"' EXIT
        mkdir -p "$stage/system/vendor/bin/hw"
        patched=$stage/system/vendor/bin/hw/android.hardware.power@1.2-service-qti
        a37_patch_hal "$original" "$patched"
        for file in apply-profile.sh post-fs-data.sh service.sh uninstall.sh; do cp "$source_dir/$file" "$stage/$file"; done
        cat > "$stage/module.prop" <<'EOF'
id=a37_power_profiles
name=A37 Balanced and Performance Profiles
version=0.1
versionCode=1
author=A37 ROM development
description=Apply battery tuning in Balanced and high CPU/GPU frequency floors in Performance.
EOF
        if [ -f "$old_cpu" ]; then cp "$old_cpu" "$stage/previous-cpu-startup.sh"; fi
        chown -R 0:0 "$stage"
        chmod 0755 "$stage" "$stage/system" "$stage/system/vendor" "$stage/system/vendor/bin" "$stage/system/vendor/bin/hw" "$patched"
        chmod 0755 "$stage/apply-profile.sh" "$stage/post-fs-data.sh" "$stage/service.sh" "$stage/uninstall.sh"
        chmod 0644 "$stage/module.prop"
        # Preserve the original HAL's SELinux file type for the overlay.
        context=$(ls -Zd "$original" | awk '{print $1}')
        case "$context" in u:object_r:*:s0) chcon "$context" "$patched";; *) fail 'Cannot establish the original HAL file context.';; esac
        mv "$stage" "$module"
        trap - EXIT
        if [ -f "$module/previous-cpu-startup.sh" ]; then rm "$old_cpu"; fi
        echo 'Profile bridge installed. Reboot to activate the Magisk overlay.'
        echo 'Original ROM partition unchanged; use remove and reboot to roll back.'
        ;;
    remove)
        owned || fail 'No recognized profile module to remove.'
        touch "$module/disable" "$module/remove"
        sh "$module/uninstall.sh"
        echo 'Profile bridge marked for removal. Reboot to restore the original HAL and startup settings.'
        ;;
esac
