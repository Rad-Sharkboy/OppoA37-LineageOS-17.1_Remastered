#!/system/bin/sh
# One-shot diagnostic only: no forced idle, battery simulation or settings writes.
printf 'A37 Android idle/scan diagnostic v1\n'
date -u
id
cat /proc/uptime
printf '\n--- Android device-idle state ---\n'
dumpsys deviceidle
printf '\n--- Scan throttling setting (null can mean default enabled) ---\n'
settings get global wifi_scan_throttle_enabled
printf '\n--- Wi-Fi/Bluetooth scanning availability ---\n'
settings get global wifi_scan_always_enabled
settings get global ble_scan_always_enabled
printf '\n--- Custom device-idle constants (null means framework defaults) ---\n'
settings get global device_idle_constants
printf '\n--- Background service runtime settings ---\n'
settings get global adaptive_battery_management_enabled
settings get global app_standby_enabled
