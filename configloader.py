#!/usr/bin/env python
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "strongMan.settings.production")
django.setup()
from strongMan.apps.server_connections.models import Connection
from strongMan.apps.eap_secrets.models import Secret
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper


def push_secrets(vici=ViciWrapper()):
    for secret in Secret.objects.all():
        vici.load_secret(secret.dict())


def push_connections():
    for connection in Connection.objects.all():
        if connection.enabled:
            connection.start()



# def push_pools(vici=ViciWrapper()):
#


def main():
    vici = ViciWrapper()
    push_secrets(vici)
    # push_pools(vici)
    push_connections()


if __name__ == "__main__":
    main()
