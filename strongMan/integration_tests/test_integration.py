import os
from strongMan.apps.certificates.container_reader import X509Reader, PKCS1Reader
from strongMan.apps.certificates.services import UserCertificateManager
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from strongMan.apps.connections.models import Connection, Child, Secret
from strongMan.apps.certificates.models.certificates import Certificate
from strongMan.apps.connections import views
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper
from strongMan.apps.vici.wrapper.exception import ViciInitiateException


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
