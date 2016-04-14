import os
from strongMan.apps.certificates.container_reader import X509Reader, PKCS1Reader
from strongMan.apps.certificates.services import UserCertificateManager
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from strongMan.apps.connections.models import Connection, IKEv2Certificate
from strongMan.apps.certificates.models.certificates import Certificate
from strongMan.apps.connections import views




class ConnectionViewTest(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.client.login(username='testuser', password='12345')
        bytes = Paths.X509_googlecom.read()
        manager = UserCertificateManager()
        manager.add_keycontainer(bytes)

        certificate = Certificate.objects.first()
        self.certificate = certificate.subclass()

        self.identity = self.certificate.identities.first()
        self.factory = RequestFactory()

    def test_select_post(self):
        response = self.client.post('/connections/add/', {'typ': 'Ike2EapForm', 'form_name': 'Ike2EapForm'})
        self.assertEquals(response.status_code, 200)

    def test_Ike2CertificateCreate_post(self):
        url = '/connections/add/create/'
        self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'certificate': self.identity.id, 'form_name': 'Ike2CertificateForm'})
        self.assertEquals(1, Connection.objects.count())

    def test_Ike2CertificateCreate_update(self):
        url_create = '/connections/add/create/'

        self.client.post(url_create, {'wizard_step': 'configure', 'gateway': "gateway", 'profile': 'profile', 'certificate': self.certificate.pk, 'identity': self.identity.pk, 'form_name': 'Ike2CertificateForm'})

        connection_created = Connection.objects.first()
        self.assertEquals(connection_created.profile, 'profile')

        url_update = '/connections/' + str(connection_created.id) + '/'
        self.client.post(url_update, {'gateway': "gateway", 'profile': 'hans', 'certificate': self.identity.id, 'form_name': 'Ike2CertificateForm'})

        connection = Connection.objects.first()
        self.assertEquals(connection.profile, 'hans')

    def test_Ike2EapCreate_post(self):
        url = '/connections/add/create/'
        self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password", 'form_name': 'Ike2EapForm'})
        self.assertEquals(1, Connection.objects.count())

    def test_Ike2EapUpdate_post(self):
        url_create = '/connections/add/create/'
        self.client.post(url_create, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password", 'form_name': 'Ike2EapForm'})
        connection_created = Connection.objects.first()
        self.assertEquals(connection_created.profile, 'profile')

        url_update = '/connections/' + str(connection_created.id) + '/'
        self.client.post(url_update, {'gateway': "gateway", 'profile': 'hans', 'username': "username", 'password': "password", 'form_name': 'Ike2EapForm'})

        connection = Connection.objects.first()
        self.assertEquals(connection.profile, 'hans')

    def test_Ike2EapCertificateCreate_post(self):
        url = '/connections/add/create/'

        self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password", 'certificate': self.identity.id, 'form_name': 'Ike2EapCertificateForm'})

        self.assertEquals(1, Connection.objects.count())

    def test_Ike2EapCertificateCreate_update(self):
        url_create = '/connections/add/create/'

        self.client.post(url_create, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password", 'certificate': self.identity.id, 'form_name': 'Ike2EapCertificateForm'})

        connection_created = Connection.objects.first()
        self.assertEquals(connection_created.profile, 'profile')

        url_update = '/connections/' + str(connection_created.id) + '/'
        self.client.post(url_update, {'gateway': "gateway", 'profile': 'hans', 'username': "username", 'password': "password", 'certificate': self.identity.id, 'form_name': 'Ike2EapCertificateForm'})

        connection = Connection.objects.first()
        self.assertEquals(connection.profile, 'hans')

    def test_delete_post(self):
        connection = IKEv2Certificate(profile='rw', auth='pubkey', version=1)
        connection.save()
        self.assertEquals(1, Connection.objects.count())
        request = self.factory.get('/')
        request.user = self.user
        views.delete_connection(request, connection.id)
        self.assertEquals(0, Connection.objects.count())

    def test_toggle_connection_post(self):
        connection = IKEv2Certificate(profile='rw', auth='pubkey', version=1)
        connection.save()
        response = self.client.post('/connections/toggle/', {'id':connection.id})
        self.assertEquals(200, response.status_code)


class TestCert:
    def __init__(self, path):
        self.path = path
        self.parent_dir = os.path.join(os.path.dirname(__file__), os.pardir)

    def read(self):
        absolute_path = self.parent_dir + "/certificates/certs/" + self.path
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
    X509_rsa_ca = TestCert("ca.crt")
    X509_rsa_ca_samepublickey_differentserialnumber = TestCert("hsrca_doppelt_gleicher_publickey.crt")
    X509_rsa_ca_samepublickey_differentserialnumber_san = TestCert("cacert_gleicher_public_anderer_serial.der")
    PKCS1_rsa_ca = TestCert("ca2.key")
    PKCS1_rsa_ca_encrypted = TestCert("ca.key")
    PKCS8_rsa_ca = TestCert("ca2.pkcs8")
    PKCS8_ec = TestCert("ec.pkcs8")
    PKCS8_rsa_ca_encrypted = TestCert("ca_enrypted.pkcs8")
    X509_rsa_ca_der = TestCert("cacert.der")
    X509_ec = TestCert("ec.crt")
    PKCS1_ec = TestCert("ec2.key")
    X509_rsa = TestCert("warrior.crt")
    PKCS12_rsa = TestCert("warrior.pkcs12")
    PKCS12_rsa_encrypted = TestCert("warrior_encrypted.pkcs12")
    X509_googlecom = TestCert("google.com_der.crt")
