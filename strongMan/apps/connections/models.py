from django.db import models
from strongMan.apps.certificates.models import Identity
from collections import OrderedDict


class Typ(models.Model):
    value = models.CharField(max_length=200)


class Connection(models.Model):
    state = models.BooleanField(default=False)
    typ = models.ForeignKey(Typ, null=True, blank=True, default=None)
    domain = models.ForeignKey(Identity, null=True, blank=True, default=None)
    profile = models.CharField(max_length=50)
    auth = models.CharField(max_length=50)
    version = models.IntegerField()

    def dict(self):
        children = OrderedDict()
        for child in self.children:
            children[child.name] = child.dict()

        ike_sa = OrderedDict()
        ike_sa['local_addrs'] = [local_address.value for local_address in self.local_addresses]
        ike_sa['remote_addrs'] = [remote_address.value for remote_address in self.remote_addresses]
        ike_sa['vips'] = [vip.value for vip in self.vips]
        ike_sa['version'] = self.version
        ike_sa['proposals'] = [proposal.type for proposal in self.proposals]
        ike_sa['children'] = children

        connection = OrderedDict()
        connection[self.profile] = ike_sa
        return connection

    def delete_all_connected_models(self):
        Secret.objects.filter(connection=self).delete()
        for child in Child.objects.filter(connection=self):
            Proposal.objects.filter(child=child).delete()
            Address.objects.filter(local_ts=child).delete()
            Address.objects.filter(remote_ts=child).delete()
            child.delete()
        Proposal.objects.filter(connection=self).delete()
        Address.objects.filter(local_addresses=self).delete()
        Address.objects.filter(remote_addresses=self).delete()
        Address.objects.filter(vips=self).delete()
        Authentication.objects.filter(local=self).delete()
        Authentication.objects.filter(remote=self).delete()

    class Meta:
        abstract = True

class Ikev2CertificateEAP(Connection):
    pass


class Child(models.Model):
    name = models.CharField(max_length=50)
    mode = models.CharField(max_length=50)
    connection = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='children')

    def dict(self):
        child = OrderedDict(mode=self.mode)
        child['local_ts'] = [local_t.value for local_t in self.local_ts]
        child['remote_ts'] = [remote_t.value for remote_t in self.remote_ts]
        child['esp_proposals'] = [esp_proposal.type for esp_proposal in self.esp_proposal]


class Secret(models.Model):
    type = models.CharField(max_length=50)
    data = models.CharField(max_length=50)
    connection = models.ForeignKey(Connection, null=True, blank=True, default=None)

    def dict(self):
        secrets = OrderedDict(type=self.type, data=self.data)
        secrets['owners'] = [owner.value for owner in self.remote_addresses]
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
    child = models.ForeignKey(Child, null=True, blank=True, default=None, related_name='esp_proposals')
    connection = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='proposals')


class Authentication(models.Model):
    local = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='local')
    remote = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='remote')
    name = models.CharField(max_length=50)  #starts with remote-* or local-*
    identity = models.CharField(max_length=200)
    auth = models.CharField(max_length=50)

    def dict(self):
        auth = OrderedDict(auth=self.auth)
        return auth

