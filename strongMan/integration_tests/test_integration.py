import os

from django.test import TestCase, Client
from django.contrib.auth.models import User

from strongMan.apps.connections.models import Connection, Child
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper
from strongMan.apps.certificates.container_reader import X509Reader, PKCS1Reader
from strongMan.apps.certificates.services import UserCertificateManager


class IntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.client.login(username='testuser', password='12345')
        self.vici_wrapper = ViciWrapper()
        self.vici_wrapper.unload_all_connections()

    def test_Ike2EapIntegration(self):
        url_create = '/connections/add/'
        self.client.post(url_create, {'wizard_step': 'configure', 'gateway': 'gateway', 'profile': 'EAP',
                                      'username': "eap-test", 'password': "Ar3etTnp", 'typ': 'Ike2EapForm'})

        self.assertEquals(1, Connection.objects.count())
        self.assertEquals(1, Child.objects.count())

        connection = Connection.objects.first().subclass()
        toggle_url = '/connections/toggle/'
        self.client.post(toggle_url, {'id': connection.id})

        self.assertEqual(self.vici_wrapper.get_connections_names().__len__(), 1)
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 1)
        self.client.post(toggle_url, {'id': connection.id})
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 0)

    def test_Ike2CertificateIntegration(self):
        url_create = '/connections/add/'
        cert = Paths.carol_cert.read()
        key = Paths.carol_key.read()
        manager = UserCertificateManager()
        manager.add_keycontainer(cert)
        manager.add_keycontainer(key)
        self.client.post(url_create, {'wizard_step': 'configure', 'gateway': 'gateway', 'profile': 'Cert',
                                      'certificate': 1, 'identity': 1, 'typ': 'Ike2CertificateForm'})
        self.assertEquals(1, Connection.objects.count())
        self.assertEquals(1, Child.objects.count())

        connection = Connection.objects.first().subclass()
        toggle_url = '/connections/toggle/'
        self.client.post(toggle_url, {'id': connection.id})

        self.assertEqual(self.vici_wrapper.get_connections_names().__len__(), 1)
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 1)
        self.client.post(toggle_url, {'id': connection.id})
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 0)

    def test_Ike2EapCertificateIntegration(self):
        url_create = '/connections/add/'
        cert = Paths.carol_cert.read()
        key = Paths.carol_key.read()
        manager = UserCertificateManager()
        manager.add_keycontainer(cert)
        manager.add_keycontainer(key)
        self.client.post(url_create, {'wizard_step': 'configure', 'gateway': 'gateway', 'profile': 'Eap+Cert',
                                      'username': "eap-test", 'password': "Ar3etTnp", 'certificate': 1, 'identity': 1,
                                      'typ': 'Ike2EapCertificateForm'})
        self.assertEquals(1, Connection.objects.count())
        self.assertEquals(1, Child.objects.count())

        connection = Connection.objects.first().subclass()
        toggle_url = '/connections/toggle/'
        self.client.post(toggle_url, {'id': connection.id})

        self.assertEqual(self.vici_wrapper.get_connections_names().__len__(), 1)
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 1)
        self.client.post(toggle_url, {'id': connection.id})
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 0)


class TestCert:
    def __init__(self, path):
        self.path = path
        self.dir = os.path.dirname(os.path.realpath(__file__))

    def read(self):
        absolute_path = self.dir + "/certs/" + self.path
        with open(absolute_path, 'rb') as f:
            return f.read()

    def read_x509(self, password=None):
        bytes = self.read()
        reader = X509Reader.by_bytes(bytes, password)
        reader.parse()
        return reader

    def read_pkcs1(self, password=None):
        bytes = self.read()
        reader = PKCS1Reader.by_bytes(bytes, password)
        reader.parse()
        return reader


class Paths:
    carol_cert = TestCert("carolCert.pem")
    carol_key = TestCert("carolKey.pem")
