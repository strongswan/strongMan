from collections import OrderedDict

from django.db import models

from strongMan.helper_apps.encryption import fields


class Secret(models.Model):
    username = models.TextField(unique=True)
    type = models.TextField()
    password = fields.EncryptedCharField(max_length=50)

    def dict(self):
        owners = []
        for owner in self.eap_tls_secret.all():
            owners.append(owner.identity.subclass().value())
        secrets = OrderedDict(type=self.type, data=self.password, id=self.username, owners=owners)
        return secrets

    def __str__(self):
        return str(self.username)
