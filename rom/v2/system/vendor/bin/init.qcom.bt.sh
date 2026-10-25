#!/vendor/bin/sh
# Optimized QCOM Bluetooth Init

POWER_CLASS=`getprop qcom.bt.dev_power_class`
LE_POWER_CLASS=`getprop qcom.bt.le_dev_pwr_class`

setprop vendor.bluetooth.status off

# Determine power classes silently
PWR_CLASS=""
case $POWER_CLASS in
  1) PWR_CLASS="-p 0" ;;
  2) PWR_CLASS="-p 1" ;;
  3) PWR_CLASS="-p 2" ;;
esac

LE_PWR_CLASS="-P 1" # Default fallback
case $LE_POWER_CLASS in
  1) LE_PWR_CLASS="-P 0" ;;
  2) LE_PWR_CLASS="-P 1" ;;
  3) LE_PWR_CLASS="-P 2" ;;
esac

# Execute HCI QCOMM Init silently and capture exit code directly
/system/vendor/bin/hci_qcomm_init -e $PWR_CLASS $LE_PWR_CLASS > /dev/null 2>&1
exit_code=$?

if [ $exit_code -eq 0 ]; then
    setprop vendor.bluetooth.status on
    exit 0
else
    setprop vendor.bluetooth.status off
    exit $exit_code
fi