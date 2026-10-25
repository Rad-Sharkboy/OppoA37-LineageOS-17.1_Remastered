#!/system/bin/sh
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 2
done
if [ ! -f /data/local/tmp/keyboard_setup_done ]; then
    settings put secure enabled_input_methods com.simplemobiletools.keyboard/.SimpleKeyboard
    settings put secure default_input_method com.simplemobiletools.keyboard/.SimpleKeyboard
    touch /data/local/tmp/keyboard_setup_done
fi