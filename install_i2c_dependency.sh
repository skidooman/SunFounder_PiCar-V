#!/bin/bash
#Installation

###################################
# Enable I2C1 #
###################################
# Add lines to /boot/config.txt
echo -e "Enalbe I2C \n"
egrep -v "^#|^$" /boot/config.txt > config.txt.temp  # pick up all uncomment configrations
if grep -q 'dtparam=i2c_arm=on' config.txt.temp; then  # whether i2c_arm in uncomment configrations or not
    echo -e '    Seem i2c_arm parameter already set, skip this step \n'
else
    echo -e '    dtparam=i2c_arm=on \n' >> /boot/config.txt
fi
rm config.txt.temp
echo -e "complete\n"

print_result

echo -e "The stuff you have change may need reboot to take effect."
echo -e "Do you want to reboot immediately? \c"
if_continue
if [ $? = 1 ]; then
    echo -e "Rebooting..."
    sudo reboot
else
    echo -e "Exiting..."
    exit
fi
