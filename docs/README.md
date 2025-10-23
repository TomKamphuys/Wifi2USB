# Your Project Name

## Description
This projects adds a wifi to usb adapter for the Near Field Scanner setup. This code can e.g. be run on a orange pi zero 3.

## Setup
Put a recent ubuntu image on the sd card as documented in the orange pi zero 3 manual.

Log in to your orange pi as root using the default root password (see manual) and update the software after installation:
```bash
apt-get update
apt-get upgrade
apt-get dist-upgrade
apt-get install python3
apt-get install python3-pip
```


### Set the hostname and use mDNS
The hostname in this example is orangepi-2. Change it to your own.

```bash
hostname orangepi-2
```

put (only) 'orangepi-2' in the file
```bash
nano /etc/hostname
```

change the line to '127.0.1.1 orangepi-2' in the file
```bash
nano /etc/hosts
```

```bash
apt-get install avahi-daemon
systemctl start avahi-daemon
systemctl enable avahi-daemon
```

Setup the wifi, replace SSID and PASSWORD with your own:
```bash
nmcli dev wifi connect SSID password PASSWORD
```


### Add a user
Create a user for the project. I used tom; change it to your own.

```bash
adduser tom
usermod -aG sudo tom
```

The esp32duino shows up on /dev/ttyUSB0 (at least on my orange pi). Add the user to the dialout group.

```bash
sudo adduser tom dialout
```

Get the code from GitHub:
```bash
git clone https://github.com/TomKamphuys/Wifi2USB.git
cd Wifi2USB
```

### Install python3.12-venv
This is needed for the virtual environment.
```bash
sudo apt-get install python3.12-venv
```

### Create a virtual environment
Create a virtual environment in the project folder.
```bash
python3 -m venv .
. ./bin/activate
```

## Installation

install websockets and grbl-streamer using pip manually

Maybe this works:
```bash
uv pip install -r requirements.txt
```

or:

```bash
uv add -r requirements.txt
```

## start the code
```bash
cd src/wifi_2_usb/
python app.py
```

## Make it run at start

Create the file autostart.sh in the home folder of the user and put this in it:

```
#!/bin/bash

cd /home/tom/Wifi2USB
source ./bin/activate
cd src/wifi_2_usb
python app.py&
```

Make the file executable:

```bash
chmod +x autostart.sh
```

Add line to crontab using the edit mode

```bash
crontab -e
```

Add this line:
@reboot /home/tom/autostart.sh
