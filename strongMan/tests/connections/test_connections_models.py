from django.test import TestCase
from strongMan.apps.connections.models import Connection, Proposal, Authentication, Child, Certificate, Address


class ConnectionModelTest(TestCase):

    def setUp(self):
        self.connection = Connection(profile='rw', auth='pubkey', version=1)
        self.connection.save()

        self.child_1 = Child(name='all', mode='TUNNEL', connection=self.connection)
        self.child_1.save()
        self.child_2 = Child(name='child_2', mode='TUNNEL', connection=self.connection)
        self.child_2.save()

        self.proposal_1 = Proposal(type='aes128gcm128-ntru128', connection=self.connection)
        self.proposal_1.save()
        self.proposal_2 = Proposal(type='aes128gcm128-ecp256', connection=self.connection)
        self.proposal_2.save()

        self.address_1 = Address(value='127.0.0.1', local_addresses=self.connection)
        self.address_2 = Address(value='127.0.0.2', remote_addresses=self.connection)
        self.address_1.save()
        self.address_2.save()

        self.remote = Authentication(name='remote-1', peer_id='home', auth='pubkey', remote=self.connection)
        self.local = Authentication(name='local-1', peer_id='home', auth='pubkey', local=self.connection)
        self.remote.save()
        self.local.save()

    def test_get_ordered_dict(self):
        print(self.connection.get_vici_ordered_dict())
        self.assertEquals(1, 1)

