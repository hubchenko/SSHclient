apt-get update
apt-get install -y wget git python-dev gcc python-pip

if [ ! -z "$1" ]
then
    pip install virtualenv
    mkdir ~/.virtualenvs
    cd ~/.virtualenvs
    virtualenv sshclient_venv --distribute
    source sshclient_venv/bin/activate
    cd sshclient_venv
fi

pip install pip==9.0.1 --upgrade
pip install setuptools --upgrade
pip install git+https://github.com/hubchenko/SSHclient.git --process-dependency-links
