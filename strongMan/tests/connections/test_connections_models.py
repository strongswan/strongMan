import os
from collections import OrderedDict
from django.test import TestCase
from strongMan.apps.connections.models import Connection, Proposal, Authentication, Child, Secret, Address, CertificateAuthentication
from strongMan.apps.certificates.models import Certificate
from strongMan.apps.certificates.container_reader import X509Reader, PKCS1Reader
from strongMan.apps.certificates.services import UserCertificateManager


class ConnectionModelTest(TestCase):
    def setUp(self):
        connection = Connection(profile='rw', auth='pubkey', version=1)
        connection.save()

        Child(name='all', mode='TUNNEL', connection=connection).save()
        Child(name='child_2', mode='TUNNEL', connection=connection).save()

        Proposal(type='aes128gcm128-ntru128', connection=connection).save()
        Proposal(type='aes128gcm128-ecp256', connection=connection).save()

        Address(value='127.0.0.1', local_addresses=connection).save()
        Address(value='127.0.0.2', remote_addresses=connection).save()

        bytes = Paths.X509_googlecom.read()
        manager = UserCertificateManager()
        manager.add_keycontainer(bytes)

        certificate = Certificate.objects.first()
        certificate = certificate.subclass()

        Authentication(name='remote-1', auth='pubkey', remote=connection).save()
        CertificateAuthentication(name='local-1', identity=certificate.identities.first(), auth='pubkey', local=connection).save()

        Secret(type='EAP', data="password", connection=connection).save()

    def test_child_added(self):
        self.assertEquals(2, Child.objects.count())

    def test_address_added(self):
        self.assertEquals(2, Address.objects.count())

    def test_connection_added(self):
        self.assertEquals(1, Connection.objects.count())

    def test_proposal_added(self):
        self.assertEquals(2, Proposal.objects.count())

    def test_authentication_added(self):
        self.assertEquals(2, Authentication.objects.count())

    def test_secret_added(self):
        self.assertEquals(1, Secret.objects.count())

    def test_connection_dict(self):
        connection = Connection.objects.first()
        self.assertTrue(isinstance(connection.dict(), OrderedDict))

    def test_secret_dict(self):
        secret = Secret.objects.first()
        self.assertTrue(isinstance(secret.dict(), OrderedDict))

    def test_delete_all_connections(self):
        connection = Connection.objects.first()

        self.assertEquals(2, Child.objects.count())
        self.assertEquals(2, Authentication.objects.count())

        connection.delete_all_connected_models()
        self.assertEquals(0, Authentication.objects.count())
        self.assertEquals(0, Child.objects.count())


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
