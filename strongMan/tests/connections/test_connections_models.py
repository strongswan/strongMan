from django.test import TestCase
from strongMan.apps.connections.models import Connection, Proposal, Authentication, Child, Secret, Address, Typ


class ConnectionModelTest(TestCase):

    def setUp(self):
        typ = Typ(name="IKEv2 Certificate")
        typ.save()
        
        connection = Connection(profile='rw', auth='pubkey', version=1, typ=typ)
        connection.save()

        Child(name='all', mode='TUNNEL', connection=connection).save()
        Child(name='child_2', mode='TUNNEL', connection=connection).save()

        Proposal(type='aes128gcm128-ntru128', connection=connection).save()
        Proposal(type='aes128gcm128-ecp256', connection=connection).save()

        Address(value='127.0.0.1', local_addresses=connection).save()
        Address(value='127.0.0.2', remote_addresses=connection).save()

        Authentication(name='remote-1', peer_id='home', auth='pubkey', remote=connection).save()
        Authentication(name='local-1', peer_id='home', auth='pubkey', local=connection).save()

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

    def test_ty_added(self):
        self.assertEquals(1, Typ.objects.count())
