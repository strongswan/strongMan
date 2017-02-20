#!/usr/bin/env python
import subprocess
import os

DJANGO_DIR = os.path.dirname(os.path.realpath(__file__))
PORT = 1515
if __name__ == "__main__":
    os.chdir(DJANGO_DIR)
    print(os.getcwd())
    print("Press CTRL + C to stop strongMan")
    print()
    cmd = DJANGO_DIR + "/env/bin/gunicorn --workers 6  --bind 0.0.0.0:" + str(PORT) + " --env DJANGO_SETTINGS_MODULE=strongMan.settings.local strongMan.wsgi:application"
    process = subprocess.check_output(cmd.split())

