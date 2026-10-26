#!/system/bin/sh
# The Power HAL runs as system; grant only the additional GPU floor control.
node=/sys/class/kgsl/kgsl-3d0/devfreq/min_freq
if [ -e "$node" ]; then
    chown 1000:1000 "$node"
    chmod 0664 "$node"
fi
