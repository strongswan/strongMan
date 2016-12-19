from collections import OrderedDict

from django.db import models

from strongMan.helper_apps.encryption import fields


class Secret(models.Model):
    username = models.TextField(unique=True)
    type = models.TextField()
    password = fields.EncryptedCharField(max_length=50)
    salt = models.TextField()

    def dict(self):
        password = self.password[32:]
        secrets = OrderedDict(type=self.type, data=password, owners=[self.username])
        return secrets

    def __str__(self):
        return str(self.username)
