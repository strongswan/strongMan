from django.test import TestCase
from collections import OrderedDict
from strongMan.apps.eap_secrets.models import Secret


class SecretModelTest(TestCase):
    def setUp(self):
        Secret(username='John', type='EAP', password='TestPassword').save()

    def test_Secret_added(self):
        self.assertEqual(1, Secret.objects.count())

    def test_secrets_encrypted_field(self):
        Secret.objects.all().delete()
        password = "adsfasdfasdf"
        secret = Secret()
        secret.type = "as"
        secret.password = password
        secret.save()

        data = Secret.objects.first().password
        self.assertEqual(data, password)

    def test_secret_dict(self):
        secret = Secret.objects.first()
        self.assertTrue(isinstance(secret.dict(), OrderedDict))
