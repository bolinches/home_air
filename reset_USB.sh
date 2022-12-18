echo -n "1-1.1.3:1.0" > /sys/bus/usb/drivers/ch341/unbind
echo 0 > /sys/bus/usb/devices/1-1.1.3/authorized
sleep 60
echo -n "1-1.1.3:1.0" > /sys/bus/usb/drivers/ch341/bind
echo 1 > /sys/bus/usb/devices/1-1.1.3/authorized
sleep 30

