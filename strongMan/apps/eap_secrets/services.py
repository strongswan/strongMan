import strongMan.apps.certificates.models.certificates
from strongMan.apps.server_connections import models

from strongMan.apps.vici.wrapper.wrapper import ViciWrapper


class EapSecretManager(models.Manager):
    def create_secret(self, name, password):
        secret = self.cre


