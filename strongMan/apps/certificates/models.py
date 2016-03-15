from django.db import models


class Certificate(models.Model):
    value = models.BinaryField()
