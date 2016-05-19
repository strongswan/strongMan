# Documentation

## setup.py
Tool to install strongMan comfortably.
```bash
./setup.py <command> [options]
```

- -v | --verbose
    - Sets the output of setup.py verbose.

### install
```bash
./setup.py install [-p %python-interpreter%]
```
Makes strongMan ready to run.

- -p | --python %python-interpreter%
    - Select a specific python interpreter to run strongMan
    - python3 is used as default value for %python-interpreter%

### uninstall
```bash
sudo ./setup.py uninstall
```
Undos the installation.
Run this command as root to remove the strongMan systemd service.

### add-service
```bash
sudo ./setup.py add-service
```
Adds strongMan as a systemd service. The service will be disabled and stopped.

Enable (start strongMan at system startup) and start it with the following commands:
```bash
sudo systemctl enable strongMan.service
sudo systemctl start strongMan.service
```

You need root permissions to run add-service.

### remove-service
```bash
sudo ./setup.py remove-service
```
Removes the strongMan systemd service.
You need root permissions to run this command.

### migrate
```bash
./setup.py migrate [-dm]
```
Runs the django migrations like descripted in [migrations](https://docs.djangoproject.com/en/1.9/topics/migrations/).
This command is mainly for developers.

- -dm | --delete-migrations
    - Deletes all old migrations scripts and also the sqlite database.