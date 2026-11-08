#!/sbin/sh
set -eu
. /tmp/prepare.sh
point=/tmp/a37-e007-system
[ ! -L "$point" ] || fail 'Unexpected update mount symlink.'
mkdir -p "$point"
mount -t ext4 -o rw "$system_block" "$point" || fail 'Cannot mount System.'
trap 'umount "$point" >/dev/null 2>&1 || true' EXIT
base=$point/system
[ -d "$base/vendor" ] && [ ! -L "$base/vendor" ] || fail 'Expected V2.1 System layout.'
grep -qxE 'ro.a37.remastered.version=2\.1(-E007)?' "$base/build.prop" || fail 'Install the working V2.1 base first.'
for path in build.prop vendor/etc/init/hw/init.qcom.power.rc vendor/etc/init/android.hardware.power@1.2-service-qti.rc vendor/bin/a37-power-profile.sh vendor/bin/hw/android.hardware.power@1.2-service-qti; do
    [ -f "$base/$path" ] && [ ! -L "$base/$path" ] || fail "Missing or unexpected target: $path"
done
trap - EXIT
