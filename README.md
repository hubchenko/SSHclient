


## SSHclient
A Python client wrapper for paramiko


#### Prerequisites
* Linux Ubuntu 14.04 server
* Python 2.7


#### Installation
```bash
wget -O install.sh https://github.com/raw/hubchenko/SSHclient/master/install.sh
chmod +x install.sh
sudo ./install.sh venv
# Note: the argument venv is optional but recommended - if specified will install all packages in a Python virtual environment
```


#### Usage
```bash
$ python
>>> from SSHclient import SSHclient
>>> client = SSHclient('hostname', 'username', 'password')

# execute command and return output as list
>>> client.execute('ifconfig')

# execute command and print output to screen
>>> client.execute('ifconfig', printout=True)

# attempt to connect to one of multiple domains - useful when attempting to connect to a
# virtual connect server where the primary is unknown
>>> client = SSHclient('fm72d-r6r14-e1', 'username', 'password', domains=['-vcff1.cps.intel.com', '-vcff2.cps.intel.com'])

# execute command and use success repsonse to determine if command was successfull
>>> client.execute('puppet -V', success_responses=[3.7.2, 4.8.4])

# can use a regex in success response as well
>>> client.execute('admintool check status', success_responses=['{regex}.*check=[0-9]*.*'])
```


#### Development Server Installation

Clone the repository
```bash
git clone https://github.com/hubchenko/SSHclient.git
cd SSHclient
```

Install packages and dependencies
```bash
chmod +x build.sh
sudo ./build.sh
source venv/bin/activate
```

Build the application
```bash
pyb
```

Link module for development
```bash
cd target/dist/SSHclient*/
python setup.py develop
```

Run unit tests
```bash
pyb run_unit_tests
```
