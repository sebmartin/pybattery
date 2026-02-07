
# PIGPIO

Needs to be compiled and installed, but venusos doesn't have the 'install' command

wget https://github.com/joan2937/pigpio/archive/master.zip
unzip master.zip
cd pigpio-master
make

mkdir -p /data/opt/pigpio
mkdir -p /data/opt/pigpio/lib
mkdir -p /data/opt/pigpio/bin
mkdir -p /data/opt/pigpio/log

cp *.so* /data/opt/pigpio/lib
cp pigpiod /data/opt/pigpio/bin

chmod +x /data/opt/pigpio/pigpio.sh
echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/data/opt/pigpio/lib /data/opt/pigpio/bin/pigpiod \"\$@\"" > /data/opt/pigpio/pigpio.sh

# Install cron job if it doesn't already exist
CRON_LINE='@reboot /data/opt/pigpio/pigpio.sh >> /data/opt/pigpio/log/pigpio.log 2>&1'
( crontab -l 2>/dev/null | grep -Fv "$CRON_LINE" ; echo "$CRON_LINE" ) | crontab -

LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/data/opt/pigpio/lib /data/opt/pigpio/bin/pigpiod --version

# DS18B20

Setup GPIO 27 for one-wire temperature sensors

```
sudo echo "dtoverlay=w1-gpio,gpiopin=27" >> /boot/config.txt
```