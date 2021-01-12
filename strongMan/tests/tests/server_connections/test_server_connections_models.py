import os

from django.test import TestCase

from strongMan.apps.certificates.models import Certificate, UserCertificate, CertificateDoNotDelete
from strongMan.apps.certificates.services import UserCertificateManager
from strongMan.apps.server_connections.models import Authentication, EapAuthentication, \
    CertificateAuthentication, CaCertificateAuthentication, Connection, IKEv2EAP, Child, Address, Proposal
from strongMan.apps.pools.models.pools import Pool

from strongMan.tests.tests.certificates.certificates import TestCertificates

class ServerConnectionModelTest(TestCase):
    def setUp(self):
        pool = Pool(poolname='testPool', addresses='10.1.0.0/16').save()

        connection = Connection(profile='rw', version='2', pool=pool, send_certreq=False, enabled=True)
        connection.save()

        child1 = Child(name='all', mode='TUNNEL', connection=connection)
        child1.save()
        child2 = Child(name='child_2', mode='TUNNEL', connection=connection)
        child2.save()

        Proposal(type='aes128gcm128-ntru128', connection=connection).save()
        Proposal(type='aes128gcm128-ecp256', connection=connection).save()

        Address(value='127.0.0.1', local_ts=child1, remote_ts=child2, local_addresses=connection).save()
        Address(value='127.0.0.2', local_ts=child1, remote_ts=child2, remote_addresses=connection).save()

        bytes = TestCertificates.X509_googlecom.read()
        manager = UserCertificateManager()
        manager.add_keycontainer(bytes)

        certificate = Certificate.objects.first().subclass()
        auth = EapAuthentication(name='local-eap', auth='eap-ttls', local=connection, round=2)
        auth.save()
        CaCertificateAuthentication(name='remote-1', auth='pubkey',
                                    ca_cert=certificate, ca_identity="adsfasdf", remote=connection).save()
        CertificateAuthentication(name='local-1', identity=certificate.identities.first(), auth='pubkey',
                                  local=connection).save()

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

    def test_delete_all_connections(self):
        connection = Connection.objects.first()

        self.assertEqual(2, Child.objects.count())
        self.assertEqual(3, Authentication.objects.count())

        connection.delete()
        self.assertEqual(0, Authentication.objects.count())
        self.assertEqual(0, Child.objects.count())

    def test_delete_all_connections_subclass(self):
        connection = IKEv2EAP(profile='rw2', version='1', send_certreq=False, enabled=True)
        connection.save()
        Child(name='all', mode='TUNNEL', connection=connection).save()

        self.assertEqual(1, IKEv2EAP.objects.count())
        self.assertEqual(3, Child.objects.count())
        self.assertEqual(2, Connection.objects.count())

        connection.delete()
        self.assertEqual(0, IKEv2EAP.objects.count())
        self.assertEqual(2, Child.objects.count())
        self.assertEqual(1, Connection.objects.count())

    def test_prevent_certificate_delete(self):
        cert = UserCertificate.objects.first()
        with self.assertRaises(CertificateDoNotDelete):
            cert.delete()

    def test_prevent_certificate_delete(self):
        UserCertificateManager.add_keycontainer(TestCertificates.X509_rsa_ca_der.read())
        cert = UserCertificate.objects.get(pk=2)
        cert.delete()
