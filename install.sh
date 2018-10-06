#!/bin/bash

if [ $(id -u) -ne 0 ]; then
  printf "Script must be run as root. Try 'sudo -H ./install.sh'\n"
  exit 1
fi

echo "Running updates"
sudo apt-get update

echo "Installing python and pillow prerequisites"
# See https://github.com/python-pillow/Pillow/blob/c28bf86b7e752a9257a0d4451ca878c1385db15c/depends/ubuntu_14.04.sh
#     Pillow/depends
sudo apt-get -y install python-dev python-setuptools cmake
sudo apt-get -y install libtiff5-dev libjpeg8-dev zlib1g-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev \
    python-tk python3-tk libharfbuzz-dev libfribidi-dev

echo "Compiling sources"
gcc Source/daemonize.c Source/main.c -lrt -lpthread -o NanoHatOLED

echo "Installing start scripts"
if [ ! -f /usr/local/bin/oled-start ]; then
    cat >/usr/local/bin/oled-start <<EOL
#!/bin/sh
EOL
    echo "cd $PWD" >> /usr/local/bin/oled-start
    echo "./NanoHatOLED" >> /usr/local/bin/oled-start
    sed -i -e '$i \/usr/local/bin/oled-start\n' /etc/rc.local
    chmod 755 /usr/local/bin/oled-start
fi


if [ ! -f BakeBit/Script/install.sh ]; then
    git submodule init
    git submodule update
fi

cd BakeBit/Script/
sudo ./install.sh

