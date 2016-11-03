
from collections import OrderedDict

from django.db import models


ATTRIBUTE_CHOICES = (
    ('dns', 'dns'),
    ('nbns', 'nbns'),
    ('dhcp', 'dhcp'),
    ('netmask', 'netmask'),
    ('server', 'server'),
    ('subnet', 'subnet'),
    ('split_include', 'split_include'),
    ('split_exclude', 'split_exclude'),
)


class Pool(models.Model):
    poolname = models.TextField(unique=True)
    addresses = models.TextField()
    attribute = models.CharField(max_length=56, choices=ATTRIBUTE_CHOICES, default='0')
    attributevalues = models.TextField()

    @classmethod
    def create(cls, poolname, addresses, attribute, attributevalues):
        pool = cls(poolname=poolname, addresses=addresses, attribute=attribute, attributevalues=attributevalues)
        return pool

    def __str__(self):
        return self

    def __repr__(self):
        return self
