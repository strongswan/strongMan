import sys
from collections import OrderedDict

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from strongMan.apps.certificates.models.identities import AbstractIdentity
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper


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

        for remote in self.remote.all():
            remote = remote.subclass()
            ike_sa.update(remote.dict())

        connection = OrderedDict()
        connection[self.profile] = ike_sa
        return connection

    def start(self):
        vici_wrapper = ViciWrapper()
        if vici_wrapper.is_connection_established(self.subclass().profile) is False:
            self._load_connection(vici_wrapper)

    def stop(self):
        vici_wrapper = ViciWrapper()
        if vici_wrapper.is_connection_established(self.profile):
            self._unload_connection(vici_wrapper)

    def _load_connection(self, vici_wrapper):
        vici_wrapper.load_connection(self.subclass().dict())

        for local in self.local.all():
            local.load_key()
            for secret in local.secret_set.all():
                vici_wrapper.load_secret(secret.dict())

        for remote in self.remote.all():
            local.load_key()
            for secret in remote.secret_set.all():
                vici_wrapper.load_secret(secret.dict())

        for child in self.children.all():
            reports = vici_wrapper.initiate(child.name, self.profile)
        self.state = True
        self.save()

    def _unload_connection(self, vici_wrapper):
        vici_wrapper.unload_connection(self.profile)
        vici_wrapper.terminate_connection(self.profile)
        self.state = False
        self.save()


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


@receiver(pre_delete, sender=Connection)
def delete_all_connected_models(sender, **kwargs):
    Secret.objects.filter(connection=sender).delete()
    for child in Child.objects.filter(connection=sender):
        Proposal.objects.filter(child=child).delete()
        Address.objects.filter(local_ts=child).delete()
        Address.objects.filter(remote_ts=child).delete()
        child.delete()
    Proposal.objects.filter(connection=sender).delete()
    Address.objects.filter(local_addresses=sender).delete()
    Address.objects.filter(remote_addresses=sender).delete()
    Address.objects.filter(vips=sender).delete()
    Authentication.objects.filter(local=sender).delete()
    Authentication.objects.filter(remote=sender).delete()


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
    authentication = models.ForeignKey(Authentication, null=True, blank=True, default=None)

    def dict(self):
        child = self.connection.subclass().children.first()
        secrets = OrderedDict(type=self.type, data=self.data, id=child.name)
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
    round = models.IntegerField(default=1)

    def dict(self):
        parameters = OrderedDict(auth=self.auth, round=self.round)
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


class CertificateAuthentication(Authentication):
    identity = models.ForeignKey(AbstractIdentity, null=True, blank=True, default=None)

    def dict(self):
        auth = super(CertificateAuthentication, self).dict()
        values = auth[self.name]
        values['certs'] = [self.identity.subclass().certificate.der_container]
        return auth

    def load_key(self):
        key = self.identity.subclass().certificate.subclass().private_key
        return OrderedDict(type=str(key.algorithm).upper(), data=key.der_container)