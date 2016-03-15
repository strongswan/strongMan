from django.db import models
from strongMan.apps.certificates.models import Certificate
import collections


class Connection(models.Model):
    state = models.BooleanField(default=False)
    profile = models.CharField(max_length=50)
    auth = models.CharField(max_length=50)
    version = models.IntegerField()
    #local_addresses = models.ManyToManyField(Address, related_name='local_addresses')
    #remote_addresses = models.ManyToManyField(Address, related_name='remote_addresses')
    #vips = models.ManyToManyField(Address, related_name='vips')
    #proposals = models.ManyToManyField(Proposal)
    #peer_authentications = models.ManyToManyField(PeerAuthentication)
    #children = models.ManyToManyField(Child)

class Child(models.Model):
    name = models.CharField(max_length=50)
    mode = models.CharField(max_length=50)
    #local_ts = models.ManyToManyField(Address, related_name='local_ts')
    #remote_ts = models.ManyToManyField(Address, related_name='remote_ts')
    #esp_proposals = models.ManyToManyField(Proposal)


class Address(models.Model):
    value = models.CharField(max_length=50)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)


class Proposal(models.Model):
    type = models.CharField(max_length=200)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)


class PeerAuthentication(models.Model):
    name = models.CharField(max_length=50)  #starts with remote-* or local-*
    peer_id = models.CharField(max_length=200)
    auth = models.CharField(max_length=50)
    #certs = models.ManyToManyField(Certificate)




    '''
    def get_vici_ordered_dict(self):
        # define child_sa
        children = collections.OrderedDict()

        # add child_sa to children
        for child in self.children.all():
            child_sa = collections.OrderedDict()
            child_sa['mode'] = child.mode
            child_sa['local_ts'] = [local_t.value for local_t in child.local_ts.all()]
            child_sa['remote_ts'] = [remote_t.value for remote_t in child.remote_ts.all()]
            child_sa['esp_proposals'] = [esp_proposal.type for esp_proposal in child.esp_proposals.all()]
            children[child.name] = child_sa

        # define ike_sa
        ike_sa = collections.OrderedDict()
        ike_sa['local_addrs'] = [local_address.value for local_address in self.local_addresses.all()]
        ike_sa['remote_addrs'] = [remote_address.value for remote_address in self.remote_addresses.all()]
        ike_sa['vips'] = [vip.value for vip in self.vips.all()]
        ike_sa['version'] = self.version
        ike_sa['proposals'] = [proposal.type for proposal in self.proposals.all()]

        for peer in self.peer_authentications.all():
            peer_auth = collections.OrderedDict()
            peer_auth['id'] = peer.peer_id
            peer_auth['auth'] = peer.auth
            peer_auth['certs'] = [cert.value for cert in peer.certs.all()]
            ike_sa[peer.name] = peer_auth

        ike_sa['children'] = children

        # define connection
        connection = collections.OrderedDict()
        connection[self.profile] = ike_sa
        return connection
    '''