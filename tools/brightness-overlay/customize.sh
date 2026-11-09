[ "$API" = 29 ] || abort "Requires the tested Android 10 ROM"
EXPECTED="0e08624a4842ea0bd7819e64c3b865598e3cc1ce20658ea816f57a06445d3908"
ACTUAL=$(sha256sum /system/framework/framework-res.apk | cut -d ' ' -f1)
[ "$ACTUAL" = "$EXPECTED" ] || abort "Framework differs from the tested A37 input"
set_perm_recursive "$MODPATH/system/product/overlay/A37Brightness" 0 0 0755 0644 u:object_r:vendor_overlay_file:s0
ui_print "Darkening delay: 8 seconds. Reboot to apply."
