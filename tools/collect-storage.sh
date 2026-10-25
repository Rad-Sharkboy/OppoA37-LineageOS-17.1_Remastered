#!/system/bin/sh
# One-shot reads only: no benchmark writes, flushes, remounts or tuning.
read_node() {
    [ -f "$1" ] && [ -r "$1" ] || return 0
    printf '\n--- %s ---\n' "$1"
    cat "$1" 2>&1
}
printf 'A37 storage/display snapshot v1\n'
date -u
id
uname -a
for prop in sys.io.scheduler persist.sys.io.scheduler sys.boot_completed vendor.post_boot.parsed ro.boottime.init ro.boottime.init.first_stage ro.boottime.init.selinux ro.boottime.init.cold_boot_wait ro.boottime.bootanim; do
    printf '%s=' "$prop"
    getprop "$prop"
done
for node in /proc/uptime /proc/partitions /proc/diskstats /proc/mounts /proc/dynamic_fsync /proc/sys/vm/dirty_ratio /proc/sys/vm/dirty_background_ratio /proc/sys/vm/dirty_bytes /proc/sys/vm/dirty_background_bytes /proc/sys/vm/dirty_expire_centisecs /proc/sys/vm/dirty_writeback_centisecs /sys/class/power_supply/battery/status /sys/class/power_supply/battery/capacity /sys/class/power_supply/battery/temp; do
    read_node "$node"
done
for block in /sys/block/mmcblk[0-9]* /sys/block/dm-*; do
    [ -d "$block" ] || continue
    # Include user-data cards and mapped volumes, not eMMC boot/RPMB areas.
    case "$block" in *boot*|*rpmb*) continue;; esac
    for field in dev size ro removable stat device/type device/name device/manfid queue/scheduler queue/read_ahead_kb queue/nr_requests queue/rotational queue/nomerges queue/rq_affinity queue/logical_block_size queue/physical_block_size queue/minimum_io_size queue/optimal_io_size queue/max_sectors_kb queue/max_hw_sectors_kb queue/discard_granularity queue/discard_max_bytes queue/iostats dm/name; do
        read_node "$block/$field"
    done
    for knob in "$block"/queue/iosched/*; do read_node "$knob"; done
    printf '\n--- %s backing devices ---\n' "$block"
    for slave in "$block"/slaves/*; do
        [ -e "$slave" ] || continue
        readlink "$slave"
    done
done
for host in /sys/kernel/debug/mmc[0-9]*; do read_node "$host/ios"; done
for field in modes mode msm_fb_panel_info dynamic_fps; do
    read_node "/sys/class/graphics/fb0/$field"
done
printf '\n--- Free space ---\n'
df -k /data /storage/emulated/0 2>&1
printf '\n--- Android volume mapping ---\n'
sm list-volumes all 2>&1
