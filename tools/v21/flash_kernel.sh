#!/sbin/sh
set -eu
. /tmp/prepare.sh
readback=/tmp/a37-v21-boot-readback.img
trap 'rm -f "$readback"' EXIT
dd if=/tmp/boot.img of="$boot_block" bs=2048 || fail 'Boot write failed.'
sync || fail 'Boot sync failed.'
dd if="$boot_block" of="$readback" bs=2048 count="$((boot_bytes / 2048))" || fail 'Boot readback failed.'
cmp /tmp/boot.img "$readback" >/dev/null 2>&1 || fail 'Boot readback differs from the package.'
echo 'V2.1: boot write verified.'
