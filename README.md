[![Build Status](https://travis-ci.org/Sebubu/strongMan.svg?branch=master)](https://travis-ci.org/Sebubu/strongMan)


# strongMan 
strongMan is a management interface for strongSwan. Based on Django and Python, strongMan provides a user friendly graphical  interface to configure and establish IPsec connections. It supports several IKEv2 authentifications
- RSA / ECDSA asymmetric encryption
- EAP with username and password
- EAP-TLS
- serveral authentification rounds

The strongMan application implements a persistent connection and asymmetric key management. Several common connection use cases are implemented and can be used in few configuration steps.

## Dependencies
- strongSwan with vici plugin (v5.4.0) <img src="https://www.strongswan.org/images/strongswan.png" width="30">
- python3
- strongMan has been developed in pure python and can be installed without any compiler
 

## Run it directly from git repository
Requirements:
- python3/pip3 or python3.5/pip3.5
- git

Run the following commands to make the server ready to run.
```bash
git clone https://github.com/Sebubu/strongMan.git
cd strongMan
sudo pip3 install -r requirements.txt
sudo ./migrate.sh -i python3
```

### Installation of the vici python egg
Actually it's relatively awkward to install the vici python egg.
We are working on some improvements with pip. But the bash commands therefore are them:
```bash
git clone -b vici-python-recv https://github.com/strongswan/strongswan.git
cd ./strongswan/src/libcharon/plugins/vici/python/
sudo python3 setup.py.in install
```


We have installed strongMan with all it's requirements and loaded a default user into the database.
Let's run the server.
```bash
python3 manage.py runserver --settings=strongMan.settings.local
```
The server is now accessible on http://localhost:8000. 
Username: John, Password: Lennon

