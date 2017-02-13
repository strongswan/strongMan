from django.db import models

ATTRIBUTE_CHOICES = (
    (None, 'None'),
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
    attribute = models.CharField(max_length=56, choices=ATTRIBUTE_CHOICES, null=True)
    attributevalues = models.TextField(null=True)

    @classmethod
    def create(cls, poolname, addresses, attribute, attributevalues):
        pool = cls(poolname=poolname, addresses=addresses, attribute=attribute,
                   attributevalues=attributevalues)
        return pool

    def dict(self):
        if self.poolname == 'radius' or self.poolname == 'dhcp':
            pools = None
        elif self.attribute is None:
            pools = {self.poolname: {'addrs': self.addresses}}
        else:
            pools = {self.poolname: {'addrs': self.addresses, self.attribute: [self.attributevalues]}}
        return pools

    def __str__(self):
        return str(self.poolname)

    def __repr__(self):
        return str(self.poolname)
