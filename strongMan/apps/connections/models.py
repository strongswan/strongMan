from django.db import models
from strongMan.apps.certificates.models import Certificate
from collections import OrderedDict


class Connection(models.Model):
    state = models.BooleanField(default=False)
    typ = models.IntegerField(default=0)
    profile = models.CharField(max_length=50)
    auth = models.CharField(max_length=50)
    version = models.IntegerField()

    def get_vici_ordered_dict(self):
        children = OrderedDict()
        for child in Child.objects.filter(connection=self):
            child_sa = OrderedDict()
            child_sa['mode'] = child.mode
            child_sa['local_ts'] = [local_t.value for local_t in Address.objects.filter(local_ts=child)]
            child_sa['remote_ts'] = [remote_t.value for remote_t in Address.objects.filter(remote_ts=child)]
            child_sa['esp_proposals'] = [esp_proposal.type for esp_proposal in Proposal.objects.filter(child=child)]
            children[child.name] = child_sa

        ike_sa = OrderedDict()
        ike_sa['local_addrs'] = [local_address.value for local_address in Address.objects.filter(local_addresses=self)]
        ike_sa['remote_addrs'] = [remote_address.value for remote_address in Address.objects.filter(remote_addresses=self)]
        ike_sa['vips'] = [vip.value for vip in Address.objects.filter(vips=self)]
        ike_sa['version'] = self.version
        ike_sa['proposals'] = [proposal.type for proposal in Proposal.objects.filter(connection=self)]

        for local in Authentication.objects.filter(local=self):
            local_auth = OrderedDict()
            local_auth['auth'] = local.auth
            #peer_auth['certs'] = [cert.value for cert in peer.certs.all()]
            ike_sa[local.name] = local_auth

        for remote in Authentication.objects.filter(remote=self):
            remote_auth = OrderedDict()
            remote_id = Address.objects.filter(remote_addresses=self).first()
            remote_auth['id'] = remote_id.value
            remote_auth['auth'] = remote.auth
            #peer_auth['certs'] = [cert.value for cert in peer.certs.all()]
            ike_sa[remote.name] = remote_auth


        ike_sa['children'] = children

        connection = OrderedDict()
        connection[self.profile] = ike_sa
        return connection


class Child(models.Model):
    name = models.CharField(max_length=50)
    mode = models.CharField(max_length=50)
    connection = models.ForeignKey(Connection)


class Secret(models.Model):
    type = models.CharField(max_length=50)
    data = models.CharField(max_length=50)
    connection = models.ForeignKey(Connection, null=True, blank=True, default=None)

    def get_vici_ordered_dict(self):
        secrets = OrderedDict()
        secrets['type'] = self.type
        secrets['data'] = self.data
        secrets['owners'] = [owner.value for owner in Address.objects.filter(remote_addresses=self.connection)]
        return secrets


class Address(models.Model):
    value = models.CharField(max_length=50)
    local_ts = models.ForeignKey(Child, null=True, blank=True, default=None, related_name='local_ts')
    remote_ts = models.ForeignKey(Child, null=True, blank=True, default=None, related_name='remote_ts')
    remote_addresses = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='remote_addresses')
    local_addresses = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='local_addresses')
    vips = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='vips')


class Proposal(models.Model):
    type = models.CharField(max_length=200)
    child = models.ForeignKey(Child, null=True, blank=True, default=None)
    connection = models.ForeignKey(Connection, null=True, blank=True, default=None)


class Authentication(models.Model):
    local = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='local')
    remote = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='remote')
    name = models.CharField(max_length=50)  #starts with remote-* or local-*
    peer_id = models.CharField(max_length=200)
    auth = models.CharField(max_length=50)
    #certs = models.ManyToManyField(Certificate)
