#!/usr/bin/env python
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "strongMan.settings.production")
django.setup()
from collections import OrderedDict
from strongMan.apps.server_connections.models import Connection
from strongMan.apps.certificates.models.certificates import PrivateKey, Certificate
from strongMan.apps.eap_secrets.models import Secret
# from strongMan.apps.pools.models.pools import Pool
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper


def load_secrets(vici=ViciWrapper()):
    for secret in Secret.objects.all():
        vici.load_secret(secret.dict())


def load_keys(vici=ViciWrapper()):
    for key in PrivateKey.objects.all():
        vici.load_key(OrderedDict(type=key.get_algorithm_type(), data=key.der_container))


def load_certificates(vici=ViciWrapper()):
    for cert in Certificate.objects.all():
        vici.load_key(OrderedDict(type=cert.get_algorithm_type(), data=cert.der_container))


def load_connections():
    for connection in Connection.objects.all():
        if connection.enabled:
            connection.start()


# def load_pools(vici=ViciWrapper()):
#   for pool in Pools:
#       vici.load_pools(pool.dict())


def load_credentials(vici=ViciWrapper()):
    load_secrets(vici)
    load_keys(vici)
    load_certificates(vici)


def main():
    vici = ViciWrapper()
    load_secrets(vici)
    # load_pools(vici)
    load_connections()


if __name__ == "__main__":
    main()
