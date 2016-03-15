from django.test import TestCase
from strongMan.apps.connections.models import Connection, Proposal, PeerAuthentication, Child, Certificate, Address


class ConfigurationsModelTest(TestCase):

    def setUp(self):
        self.proposal_1 = Proposal(type='aes128gcm128-ntru128')
        self.proposal_1.save()
        self.proposal_2 = Proposal(type='aes128gcm128-ecp256')
        self.proposal_2.save()

        self.address_1 = Address(value='127.0.0.1')
        self.address_2 = Address(value='127.0.0.2')
        self.address_1.save()
        self.address_2.save()

        self.remote = PeerAuthentication(name='remote-1', peer_id='home', auth='pubkey')
        self.local = PeerAuthentication(name='local-1', peer_id='home', auth='pubkey')
        self.remote.save()
        self.local.save()

        self.child_1 = Child(name='all', mode='TUNNEL')
        self.child_1.save()
        self.child_2 = Child(name='child_2', mode='TUNNEL')
        self.child_2.save()
        self.child_1.local_ts.add(self.address_1)
        self.child_1.local_ts.add(self.address_2)
        self.child_1.remote_ts.add(self.address_2)
        self.child_1.esp_proposals.add(self.proposal_1)
        self.child_1.esp_proposals.add(self.proposal_2)

        self.configuration = Connection(profile='rw', auth='pubkey', version=1)
        self.configuration.save()
        self.configuration.children.add(self.child_1)
        self.configuration.children.add(self.child_2)
        self.configuration.local_addresses.add(self.address_1)
        self.configuration.local_addresses.add(self.address_2)
        self.configuration.remote_addresses.add(self.address_2)
        self.configuration.vips.add(self.address_1)
        self.configuration.proposals.add(self.proposal_1)
        self.configuration.proposals.add(self.proposal_2)
        self.configuration.peer_authentications.add(self.remote)
        self.configuration.peer_authentications.add(self.local)

    def test_get_ordered_dict(self):
        print(self.configuration.get_vici_ordered_dict())
        self.assertEquals(1, 1)

