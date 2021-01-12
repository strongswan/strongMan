import os
from collections import OrderedDict

from django.test import TestCase

from strongMan.apps.certificates.models import Certificate, UserCertificate, CertificateDoNotDelete
from strongMan.apps.certificates.services import UserCertificateManager
from strongMan.apps.connections.models.authentication import Authentication, EapAuthentication, \
    CertificateAuthentication, CaCertificateAuthentication
from strongMan.apps.connections.models.connections import Connection, IKEv2EAP
from strongMan.apps.connections.models.specific import Child, Address, Proposal, Secret

from strongMan.tests.tests.certificates.certificates import TestCertificates


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

        bytes = TestCertificates.X509_googlecom.read()
        manager = UserCertificateManager()
        manager.add_keycontainer(bytes)

        certificate = Certificate.objects.first().subclass()
        auth = EapAuthentication(name='local-eap', auth='eap', local=connection, eap_id='hans', round=2)
        auth.save()
        CaCertificateAuthentication(name='remote-1', auth='pubkey',
                                    ca_cert=certificate, ca_identity="adsfasdf", remote=connection).save()
        CertificateAuthentication(name='local-1', identity=certificate.identities.first(), auth='pubkey',
                                  local=connection).save()
        Secret(type='EAP', data="password", authentication=auth).save()

    def test_child_added(self):
        self.assertEqual(2, Child.objects.count())

    def test_address_added(self):
        self.assertEqual(2, Address.objects.count())

    def test_connection_added(self):
        self.assertEqual(1, Connection.objects.count())

    def test_proposal_added(self):
        self.assertEqual(2, Proposal.objects.count())

    def test_authentication_added(self):
        self.assertEqual(3, Authentication.objects.count())

    def test_secret_added(self):
        self.assertEqual(1, Secret.objects.count())

    def test_connection_dict(self):
        connection = Connection.objects.filter(profile='rw').first()
        self.assertTrue(isinstance(connection.dict(), OrderedDict))

    def test_secret_dict(self):
        secret = Secret.objects.first()
        self.assertTrue(isinstance(secret.dict(), OrderedDict))

    def test_delete_all_connections(self):
        connection = Connection.objects.first()

        self.assertEqual(2, Child.objects.count())
        self.assertEqual(3, Authentication.objects.count())

        connection.delete()
        self.assertEqual(0, Authentication.objects.count())
        self.assertEqual(0, Child.objects.count())

    def test_delete_all_connections_subclass(self):
        connection = IKEv2EAP(profile='eap', auth='pubkey', version=1)
        connection.save()
        Child(name='all', mode='TUNNEL', connection=connection).save()

        self.assertEqual(1, IKEv2EAP.objects.count())
        self.assertEqual(3, Child.objects.count())
        self.assertEqual(2, Connection.objects.count())

        connection.delete()
        self.assertEqual(0, IKEv2EAP.objects.count())
        self.assertEqual(2, Child.objects.count())
        self.assertEqual(1, Connection.objects.count())

    def test_secrets_encrypted_field(self):
        Secret.objects.all().delete()
        password = "adsfasdfasdf"
        secret = Secret()
        secret.type = "as"
        secret.data = password
        secret.save()

        data = Secret.objects.first().data
        self.assertEqual(data, password)

    def test_prevent_certificate_delete(self):
        cert = UserCertificate.objects.first()
        with self.assertRaises(CertificateDoNotDelete):
            cert.delete()

    def test_prevent_certificate_delete(self):
        UserCertificateManager.add_keycontainer(TestCertificates.X509_rsa_ca_der.read())
        cert = UserCertificate.objects.get(pk=2)
        cert.delete()
