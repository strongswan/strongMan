
from collections import OrderedDict

from django.db import models


class Pool(models.Model):
    name = models.TextField(unique=True)
    address = models.TextField()

    def dict(self):
        children = OrderedDict()
        for child in self.children.all():
            children[child.name] = child

        return children

    def __str__(self):
        return self.name
