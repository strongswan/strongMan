import sys
from django.db import models
from strongMan.apps.certificates.models.identities import AbstractIdentity
from collections import OrderedDict


class Connection(models.Model):
    state = models.BooleanField(default=False)
    profile = models.CharField(max_length=50, unique=True)
    auth = models.CharField(max_length=50)
    version = models.IntegerField()

    def dict(self):
        children = OrderedDict()
        for child in self.children.all():
            children[child.name] = child.dict()

        ike_sa = OrderedDict()
        #ike_sa['local_addrs'] = [local_address.value for local_address in self.local_addresses.all()]
        ike_sa['remote_addrs'] = [remote_address.value for remote_address in self.remote_addresses.all()]
        ike_sa['vips'] = [vip.value for vip in self.vips.all()]
        ike_sa['version'] = self.version
        ike_sa['proposals'] = [proposal.type for proposal in self.proposals.all()]
        ike_sa['children'] = children

        for local in self.local.all():
            local = local.subclass()
            ike_sa.update(local.dict())

        '''
        for remote in self.remote.all():
            remote = remote.subclass()
            ike_sa.update(remote.dict())
        '''
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

    @classmethod
    def get_types(cls):
        subclasses = [subclass() for subclass in cls.__subclasses__()]
        return [subclass.get_typ() for subclass in subclasses]

    def get_typ(self):
        return type(self).__name__

    def subclass(self):
        for cls in self.get_types():
            connection_class = getattr(sys.modules[__name__], cls)
            connection = connection_class.objects.filter(id=self.id)
            if connection:
                return connection.first()
        return self


class IKEv2Certificate(Connection):
    pass


class IKEv2EAP(Connection):
    pass

class IKEv2CertificateEAP(Connection):
    pass


class Child(models.Model):
    name = models.CharField(max_length=50)
    mode = models.CharField(max_length=50)
    connection = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='children')

    def dict(self):
        child = OrderedDict()
        #child['local_ts'] = [local_t.value for local_t in self.local_ts.all()]
        #child['remote_ts'] = [remote_t.value for remote_t in self.remote_ts.all()]
        child['esp_proposals'] = [esp_proposal.type for esp_proposal in self.esp_proposals.all()]
        return child


class Secret(models.Model):
    type = models.CharField(max_length=50)
    data = models.CharField(max_length=50)
    connection = models.ForeignKey(Connection, null=True, blank=True, default=None)

    def dict(self):
        secrets = OrderedDict(type=self.type, data=self.data, id='eap-test')
        #secrets['lers'] = [owner.value for owner in self.connection.remote_addresses.all()]
        #secrets['owners'] = [owner.value for owner in self.connection.local_addresses.all()]
        return secrets


class Address(models.Model):
    value = models.CharField(max_length=50)
    local_ts = models.ForeignKey(Child, null=True, blank=True, default=None, related_name='local_ts')
    remote_ts = models.ForeignKey(Child, null=True, blank=True, default=None, related_name='remote_ts')
    remote_addresses = models.ForeignKey(Connection, null=True, blank=True, default=None,
                                         related_name='remote_addresses')
    local_addresses = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='local_addresses')
    vips = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='vips')


class Proposal(models.Model):
    type = models.CharField(max_length=200)
    child = models.ForeignKey(Child, null=True, blank=True, default=None, related_name='esp_proposals')
    connection = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='proposals')


class Authentication(models.Model):
    local = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='local')
    remote = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='remote')
    name = models.CharField(max_length=50)  # starts with remote-* or local-*
    auth = models.CharField(max_length=50)
    identity = models.ForeignKey(AbstractIdentity, null=True, blank=True, default=None)

    def dict(self):
        parameters = OrderedDict(auth=self.auth)
        auth = OrderedDict()
        auth[self.name] = parameters
        return auth

    @classmethod
    def get_types(cls):
        subclasses = [subclass() for subclass in cls.__subclasses__()]
        return [subclass.get_typ() for subclass in subclasses]

    def get_typ(self):
        return type(self).__name__

    def subclass(self):
        for cls in self.get_types():
            authentication_class = getattr(sys.modules[__name__], cls)
            authentication = authentication_class.objects.filter(id=self.id)
            if authentication:
                return authentication.first()
        return self


class EapAuthentication(Authentication):
    eap_id = models.CharField(max_length=50)

    def dict(self):
        auth = super(EapAuthentication, self).dict()
        values = auth[self.name]
        values['eap_id'] = self.eap_id
        return auth