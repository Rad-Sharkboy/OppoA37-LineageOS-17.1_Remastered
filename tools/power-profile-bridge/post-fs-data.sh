#!/system/bin/sh
# The native Power HAL runs as system.
for node in /sys/class/kgsl/kgsl-3d0/devfreq/min_freq /sys/class/kgsl/kgsl-3d0/default_pwrlevel; do
    if [ -e "$node" ]; then
        chown 1000:1000 "$node"
        chmod 0664 "$node"
    fi
done
