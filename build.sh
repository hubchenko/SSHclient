#!/bin/bash
set -e

# run script only as root
if [ $(id -u) != 0 ]; then
    echo "This script must be run as root"
    exit 1
fi

# install required packages
apt-get update
apt-get install -y gcc python-dev python-virtualenv

# create and activate virtual environment
virtualenv venv
. venv/bin/activate

# install latest version of pip
wget -Oget-pip.py https://bootstrap.pypa.io/get-pip.py
python get-pip.py
rm -r get-pip.py

# install pybuilder
git clone https://github.com/pybuilder/pybuilder.git pyb
cd pyb/
python setup.py install
cd ..
rm -rf pyb/

pyb install_dependencies
pyb clean
pyb analyze
pyb run_unit_tests

user="${SUDO_USER:-$USER}"
group=`groups $user | awk -F' ' '{print $3}'`
# change ownership of venv and target directories
chown -R $user:$group target
chown -R $user:$group venv