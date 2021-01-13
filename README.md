[![Build Status](https://github.com/strongswan/strongMan/workflows/CI/badge.svg)](https://github.com/strongswan/strongMan/actions?query=workflow%3ACI)
[![Coverage Status](https://coveralls.io/repos/github/strongswan/strongMan/badge.svg?branch=master)](https://coveralls.io/github/strongswan/strongMan?branch=master)


# strongMan
strongMan is a management interface for strongSwan. Based on Django and Python, strongMan provides a user friendly graphical  interface to configure and establish IPsec connections. It supports
- RSA / ECDSA asymmetric encryption
- EAP with username and password
- EAP-TLS
- serveral authentification rounds

The strongMan application implements a persistent connection and asymmetric key management. Several common connection use cases are implemented and can be used in few configuration steps.

## Run it directly from git repository
Requirements:
- strongSwan with vici plugin <img src="https://www.strongswan.org/images/strongswan.png" width="30">
- python3/pip3
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html)

Run the following commands to install strongMan.
```bash
git clone https://github.com/strongswan/strongMan.git
cd strongMan
sudo ./setup.py install
```
We have installed strongMan with all it's requirements in a virtual environment and loaded a default user into the database.

### Configuration Loader
To guarantee data consistency between strongMan and strongSwan, configure a script in the strongSwan configuration, which will be executed on the startup of strongSwan.

##### Option 1
If you aren’t planning on setting up a systemd service, do the following: Put these lines into
in "/etc/strongswan.d/strongMan.conf". Replace ’pathTostrongMan’ with the path, where you
installed strongMan.
```
charon {
  start-scripts {
    strongman = /pathTostrongMan/configloader.py
  }
}
```
##### Option 2
If you will configure strongMan with a systemd service, follow these instructions to get the
Configuration Loader running.
Put the following line into "strongswan-swanctl.service". Replace "pathTostrongMan" with the path, where you installed strongMan.
```
ExecStartPost=/pathTostrongMan/configloader.py
```

### Run

Now we can start the strongMan server.
```bash
sudo ./run.py
```
The server is now accessible on http://localhost:1515
Username: John, Password: Lennon@1940


### Add a systemd service
If you want to run strongMan permanently in the background you can install strongMan as a systemd service.
```bash
sudo ./setup.py add-service # Adds the service and additionally a launcher icon
```

### Remove service
Removes the service and the launcher icon
```bash
sudo ./setup.py remove-service
```
