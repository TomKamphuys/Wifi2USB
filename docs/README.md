# Your Project Name

## Description
This projects adds a wifi to usb adapter for the Near Field Scanner setup. This code can e.g. be run on a orange pi zero 3.

## Setup
Put a recent ubuntu image on the sd card as documented in the orange pi zero 3 manual.

Log in to your orange pi as root using the default root password (see manual) and update the software after installation:

### Set the hostname and use mDNS
The hostname in this example is orangepi-2. Change it to your own.

```bash
hostname orangepi-2
```

put (only) 'orangepi-2' in the file
```bash
nano /etc/hostname
```

add '127.0.0.1 orangepi-2' in the file
```bash
nano /etc/hosts
```

```bash
apt-get install avahi-daemon
systemctl start avahi-daemon
systemctl enable avahi-daemon
```

### Add a user
Create a user for the project. I used tom; change it to your own.

```bash
adduser tom
usermod -aG sudo tom
```


## Installation
```bash
pip install -r requirements.txt
```