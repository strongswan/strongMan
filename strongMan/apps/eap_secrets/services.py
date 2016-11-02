from strongMan.apps.server_connections import models


class EapSecretManager(models.Manager):
    def create_secret(self, name, password):
        secret = self.cre


