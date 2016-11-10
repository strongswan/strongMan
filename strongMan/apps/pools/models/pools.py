from django.db import models

ATTRIBUTE_CHOICES = (
    ('None', 'None'),
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
    attribute = models.CharField(max_length=56, choices=ATTRIBUTE_CHOICES)
    attributevalues = models.TextField()

    @classmethod
    def create(cls, poolname, addresses, attribute, attributevalues):
        pool = cls(poolname=poolname, addresses=addresses, attribute=attribute, attributevalues=attributevalues)
        return pool

    def __str__(self):
        return str(self.poolname)

    def __repr__(self):
        return str(self.poolname)

    # def dict(self):
    #     attributevalues_list = OrderedDict()
    #     attributevalues_list = 'd'
    #     pools = OrderedDict(poolname=self.poolname,
        # addresses=self.addresses, attribute=self.attribute, self.attributevalues)
    #     return pools

    # on delete: pool.related_name.all...

