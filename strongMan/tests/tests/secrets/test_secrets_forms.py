from django.test import TestCase
from strongMan.apps.eap_secrets.models.secrets import Secret
from strongMan.apps.eap_secrets.forms import AddOrEditForm


class SecretModelTest(TestCase):
    def setUp(self):
        Secret(username='John', type='EAP', password='TestPassword').save()

    def test_AddOrEditForm(self):
        form_data = {'username': 'John', 'password': 'Password'}
        form = AddOrEditForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_AddOrEditForm_invalid(self):
        form_data = {'username': 'John', 'password': ''}
        form = AddOrEditForm(data=form_data)
        self.assertFalse(form.is_valid())
