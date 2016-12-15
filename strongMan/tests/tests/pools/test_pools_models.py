from django.test import TestCase
from collections import OrderedDict
from strongMan.apps.pools.models import Pool


class SecretModelTest(TestCase):
    def setUp(self):
        Pool(poolname='pool', addresses='192.168.0.5', attribute='dns', attributevalues='192.168.0.6').save()
        Pool.create('pool2', '192.168.0.7', 'dhcp', '192.168.0.8').save()

    def test_pool_added(self):
        self.assertEqual(2, Pool.objects.count())

    def test_pool_attribute(self):
        self.assertEqual('dns', Pool.objects.first().attribute)

    def test_pool_attributevalues(self):
        self.assertEqual('192.168.0.6', Pool.objects.first().attributevalues)
