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
- [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html)

Run the following commands to make the server ready to run.
```bash
git clone https://github.com/Sebubu/strongMan.git
cd strongMan
./strongMan.sh install # Type in your python interpreter if you get asked.
```

We have installed strongMan with all it's requirements in a virtual environment and loaded a default user into the database.
Let's run the server.
```bash
./strongMan.sh runserver
```
The server is now accessible on http://localhost:8000. 
Username: John, Password: Lennon

