from django.test import TestCase
from strongMan.apps.pools.models.pools import Pool
from strongMan.apps.pools.forms import AddOrEditForm


class SecretModelTest(TestCase):

    def test_AddOrEditForm(self):
        form_data = {'poolname': 'pool', 'addresses': '192.168.0.5', 'attribute': 'None'}
        form = AddOrEditForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_AddOrEditForm_invalid(self):
        form_data = {'poolname': 'pool', 'addresses': 'AllOfMyAddresses'}
        form = AddOrEditForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_AddOrEditForm_attribute(self):
        form_data = {'poolname': 'pool', 'addresses': '192.168.0.5', 'attribute': 'dns',
                     'attributevalues': '192.168.0.8'}
        form = AddOrEditForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_AddOrEditForm_address_ranges(self):
        form_data = {'poolname': 'pool', 'addresses': '192.168.0.5-192.168.0.8', 'attribute': 'None'}
        form = AddOrEditForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_AddOrEditForm_address_ranges_cidr(self):
        form_data = {'poolname': 'pool', 'addresses': '192.168.0.5/24', 'attribute': 'None'}
        form = AddOrEditForm(data=form_data)
        self.assertTrue(form.is_valid())
