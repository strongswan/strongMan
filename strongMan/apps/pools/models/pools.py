
from django.db import models


class Pool(models.Model):
    poolname = models.TextField(unique=True)
    addresses = models.TextField()

    @classmethod
    def create(cls, poolname, addresses):
        pool = cls(poolname=poolname, addresses=addresses)
        # do something with the pool
        return pool

    def clean(self):
        if self.poolname:
            self.poolname = self.poolname.strip()

    def __str__(self):
        return self

    def __repr__(self):
        return self
