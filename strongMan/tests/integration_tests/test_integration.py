import os

from django.contrib.auth.models import User
from django.test import TestCase, Client

from strongMan.apps.certificates.container_reader import X509Reader
from strongMan.apps.certificates.models.certificates import Certificate
from strongMan.apps.certificates.services import UserCertificateManager
from strongMan.apps.connections.models.connections import Connection
from strongMan.apps.connections.models.specific import Child
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper

from strongMan.tests.utils.certificates import CertificateLoader


class TestCertificates(object):
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "certs")
    loader = CertificateLoader(path)
    carol_cert = loader.create("carolCert.pem")
    carol_key = loader.create("carolKey.pem")
    strongSwan_cert = loader.create("strongswanCert.pem")


class IntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.client.login(username='testuser', password='12345')
        ca_cert = TestCertificates.strongSwan_cert.read()
        cert = TestCertificates.carol_cert.read()
        key = TestCertificates.carol_key.read()
        manager = UserCertificateManager()
        manager.add_keycontainer(cert)
        manager.add_keycontainer(key)
        manager.add_keycontainer(ca_cert)
        for c in Certificate.objects.all():
            if "carol@strongswan" in str(c.der_container):
                self.carol_cert = c
            else:
                self.ca_cert = c

        for i in self.carol_cert.identities:
            if str(i.subclass()) == 'carol@strongswan.org':
                self.carol_ident = i.subclass()
        self.vici_wrapper = ViciWrapper()
        self.vici_wrapper.unload_all_connections()

    def test_certificates_are_loaded(self):
        certificates = self.vici_wrapper.get_certificates()
        self.assertTrue(len(certificates) > 0)

    def test_Ike2EapIntegration(self):
        url_create = '/connections/add/'
        response = self.client.post(url_create, {'current_form': 'Ike2EapForm', 'gateway': 'gateway', 'profile': 'EAP',
                                                 'certificate_ca': self.ca_cert.pk,
                                                 'identity_ca': "moon.strongswan.org",
                                                 'username': "eap-test", 'password': "test"})

        print(response.content.decode('utf-8'))
        self.assertEqual(1, Connection.objects.count())
        self.assertEqual(1, Child.objects.count())

        connection = Connection.objects.first().subclass()
        toggle_url = '/connections/toggle/'
        self.client.post(toggle_url, {'id': connection.id})

        self.assertEqual(self.vici_wrapper.get_connections_names().__len__(), 1)
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 1)
        self.client.post(toggle_url, {'id': connection.id})
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 0)

    def test_Ike2Eap_auto_ca(self):
        url_create = '/connections/add/'
        response = self.client.post(url_create, {'current_form': 'Ike2EapForm', 'gateway': 'gateway', 'profile': 'EAP',
                                                 'certificate_ca_auto': True, 'identity_ca': "moon.strongswan.org",
                                                 'username': "eap-test", 'password': "test"})

        print(response.content.decode('utf-8'))
        self.assertEqual(1, Connection.objects.count())
        self.assertEqual(1, Child.objects.count())

        connection = Connection.objects.first().subclass()
        toggle_url = '/connections/toggle/'
        self.client.post(toggle_url, {'id': connection.id})

        self.assertEqual(self.vici_wrapper.get_connections_names().__len__(), 1)
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 1)
        self.client.post(toggle_url, {'id': connection.id})
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 0)

    def test_Ike2CertificateIntegration(self):
        url_create = '/connections/add/'

        self.client.post(url_create, {'gateway': 'gateway', 'profile': 'Cert',
                                      'certificate': self.carol_cert.pk, 'identity': self.carol_ident.pk,
                                      'certificate_ca': self.ca_cert.pk, 'identity_ca': "moon.strongswan.org",
                                      'current_form': 'Ike2CertificateForm'})
        self.assertEqual(1, Connection.objects.count())
        self.assertEqual(1, Child.objects.count())

        connection = Connection.objects.first().subclass()

        toggle_url = '/connections/toggle/'
        self.client.post(toggle_url, {'id': connection.id})

        self.assertEqual(self.vici_wrapper.get_connections_names().__len__(), 1)
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 1)
        self.client.post(toggle_url, {'id': connection.id})
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 0)

    def test_Ike2EapCertificateIntegration(self):
        url_create = '/connections/add/'
        self.client.post(url_create, {'gateway': 'gateway', 'profile': 'Eap+Cert',
                                      'username': "eap-test", 'password': "test",
                                      'certificate': self.carol_cert.pk,
                                      'identity': self.carol_cert.identities.first().pk,
                                      'certificate_ca': self.ca_cert.pk, 'identity_ca': "moon.strongswan.org",
                                      'current_form': 'Ike2EapCertificateForm'})
        self.assertEqual(1, Connection.objects.count())
        self.assertEqual(1, Child.objects.count())

        connection = Connection.objects.first().subclass()

        toggle_url = '/connections/toggle/'
        self.client.post(toggle_url, {'id': connection.id})

        self.assertEqual(self.vici_wrapper.get_connections_names().__len__(), 1)
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 1)
        self.client.post(toggle_url, {'id': connection.id})
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 0)

    def test_Ike2EapTlsIntegration(self):
        url_create = '/connections/add/'
        self.client.post(url_create, {'gateway': 'gateway', 'profile': 'Eap+Tls',
                                      'certificate': self.carol_cert.pk,
                                      'identity': self.carol_cert.identities.first().pk,
                                      'certificate_ca': self.ca_cert.pk, 'identity_ca': "moon.strongswan.org",
                                      'current_form': 'Ike2EapTlsForm'})
        self.assertEqual(1, Connection.objects.count())
        self.assertEqual(1, Child.objects.count())

        connection = Connection.objects.first().subclass()
        toggle_url = '/connections/toggle/'
        self.client.post(toggle_url, {'id': connection.id})

        self.assertEqual(self.vici_wrapper.get_connections_names().__len__(), 1)
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 1)
        self.client.post(toggle_url, {'id': connection.id})
        self.assertEqual(self.vici_wrapper.get_sas().__len__(), 0)

    def test_logs(self):
        self._start_connection()
        logs = self.client.post('/connections/log/', {'id': -1})
        self.assertTrue(len(logs._container) > 0)

    def test_logs(self):
        self._start_connection()
        url = '/connections/log/'
        logs = self.client.post(url, {'id': -1})
        self.assertTrue(len(logs._container) > 0)

    def test_sa_info(self):
        self._start_connection()
        url = '/connections/info/'
        connection = Connection.objects.first().subclass()

        info = self.client.post(url, {'id': connection.id})
        self.assertTrue(len(info._container) > 0)

    def test_overview(self):
        self._start_connection()
        url = '/connections/'

        overview = self.client.get(url)
        self.assertEqual(overview.status_code, 200)

    def test_state(self):
        self._start_connection()
        connection = Connection.objects.first().subclass()
        url = '/connections/state/' + str(connection.id) + '/'

        state = self.client.post(url)
        self.assertEqual(state.status_code, 200)

    def _start_connection(self):
        url_create = '/connections/add/'
        self.client.post(url_create, {'gateway': 'gateway', 'profile': 'Eap+Tls',
                                      'certificate': self.carol_cert.pk,
                                      'identity': self.carol_cert.identities.first().pk,
                                      'certificate_ca': self.ca_cert.pk, 'identity_ca': "moon.strongswan.org",
                                      'current_form': 'Ike2EapTlsForm'})
        self.assertEqual(1, Connection.objects.count())
        self.assertEqual(1, Child.objects.count())

        connection = Connection.objects.first().subclass()
        toggle_url = '/connections/toggle/'
        self.client.post(toggle_url, {'id': connection.id})
