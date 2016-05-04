import sys
from enum import Enum
from collections import OrderedDict

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from strongMan.apps.certificates.models.identities import AbstractIdentity, DnIdentity
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper
from strongMan.apps.encryption import fields
from ..certificates.models import UserCertificate, PrivateKey, CertificateDoNotDelete, MessageObj


class DjangoEnum(Enum):
    @classmethod
    def choices(cls):
        return [(x.value, x.name) for x in cls]


class State(DjangoEnum):
    DOWN = 'DOWN'
    CONNECTING = 'CONNECTING'
    ESTABLISHED = 'ESTABLISHED'

class CertConDoNotDeleteMessage(MessageObj):
    def __init__(self, connection):
        self.connection = connection

    def __str__(self):
        return "Certificate is in use by the connection named '" + self.connection.profile + "'."

class KeyConDoNotDeleteMessage(MessageObj):
    def __init__(self, connection):
        self.connection = connection

    def __str__(self):
        return "Private key is in use by the connection named '" + self.connection.profile + "'."



@receiver(UserCertificate.should_prevent_delete_signal, sender=UserCertificate)
def prevent_cert_delete_if_cert_is_in_use(sender, **kwargs):
    cert = kwargs['instance']
    authentications = [ident.tls_identity for ident in cert.identities] + [ident.cert_identity for ident in cert.identities] + [cert.ca_cert_authentication]

    for auth in authentications:
        if auth.count() > 0:
            raise CertificateDoNotDelete(CertConDoNotDeleteMessage(auth.first().connection))
    return False, ""

@receiver(PrivateKey.should_prevent_delete_signal, sender=PrivateKey)
def prevent_key_delete_if_cert_is_in_use(sender, **kwargs):
    cert = kwargs['usercertificate']
    authentications = [ident.tls_identity for ident in cert.identities] + [ident.cert_identity for ident in
                                                                           cert.identities]
    for auth in authentications:
        if auth.count() > 0:
            raise CertificateDoNotDelete(KeyConDoNotDeleteMessage(auth.first().connection))
    return False, ""



class Connection(models.Model):
    state = models.CharField(max_length=15, choices=State.choices())
    profile = models.CharField(max_length=50, unique=True)
    auth = models.CharField(max_length=50)
    version = models.IntegerField()

    def dict(self):
        children = OrderedDict()
        for child in self.children.all():
            children[child.name] = child.dict()

        ike_sa = OrderedDict()
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
        vici_wrapper.load_connection(self.subclass().dict())

        for local in self.local.all():
            local = local.subclass()
            if local.has_private_key():
                vici_wrapper.load_key(local.get_key_dict())
            for secret in Secret.objects.filter(authentication=local):
                vici_wrapper.load_secret(secret.dict())

        for remote in self.remote.all():
            remote = remote.subclass()
            if remote.has_private_key():
                vici_wrapper.load_key(remote.get_key_dict())
            for secret in Secret.objects.filter(authentication=remote):
                vici_wrapper.load_secret(secret.dict())

        for child in self.children.all():
            logs = vici_wrapper.initiate(child.name, self.profile)
            for log in logs:
                LogMessage(connection=self, message=log['message'], level=log['level']).save()
        self.state = State.ESTABLISHED.value
        self.save()

    def stop(self):
        vici_wrapper = ViciWrapper()
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

    @classmethod
    def choice_name(cls):
        raise NotImplementedError


@receiver(pre_delete, sender=Connection)
def delete_all_connected_models(sender, **kwargs):
    for child in Child.objects.filter(connection=sender):
        Proposal.objects.filter(child=child).delete()
        Address.objects.filter(local_ts=child).delete()
        Address.objects.filter(remote_ts=child).delete()
        child.delete()
    Proposal.objects.filter(connection=sender).delete()
    Address.objects.filter(local_addresses=sender).delete()
    Address.objects.filter(remote_addresses=sender).delete()
    Address.objects.filter(vips=sender).delete()

    for local in Authentication.objects.filter(local=sender):
        for secret in Secret.objects.filter(authentication=local):
            secret.delete()
        local.delete()

    for remote in Authentication.objects.filter(remote=sender):
        for secret in Secret.objects.filter(authentication=remote):
            secret.delete()
        remote.delete()


class IKEv2Certificate(Connection):
    @classmethod
    def choice_name(cls):
        return "IKEv2 Certificate"


class IKEv2EAP(Connection):
    @classmethod
    def choice_name(cls):
        return "IKEv2 EAP (Username/Password)"


class IKEv2CertificateEAP(Connection):
    @classmethod
    def choice_name(cls):
        return "IKEv2 Certificate + EAP (Username/Password)"


class IKEv2EapTls(Connection):
    @classmethod
    def choice_name(cls):
        return "IKEv2 EAP-TLS (Certificate)"


class Child(models.Model):
    name = models.CharField(max_length=50)
    mode = models.CharField(max_length=50)
    connection = models.ForeignKey(Connection, null=True, blank=True, default=None, related_name='children')

    def dict(self):
        child = OrderedDict()
        child['remote_ts'] = [remote_t.value for remote_t in self.remote_ts.all()]
        child['esp_proposals'] = [esp_proposal.type for esp_proposal in self.esp_proposals.all()]
        return child


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
    ca_cert = models.ForeignKey(UserCertificate, null=True, blank=True, default=None, related_name='ca_cert_authentication')
    ca_identity = models.TextField()

    @property
    def connection(self):
        if self.local is not None:
            return self.local
        elif self.remote is not None:
            return self.remote
        else:
            return None

    def dict(self):
        parameters = OrderedDict(auth=self.auth, round=self.round)
        if self.ca_cert is not None:
            parameters['certs'] = [self.ca_cert.der_container]
            parameters['id'] = self.ca_identity
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

    def has_private_key(self):
        return False

    def get_key_dict(self):
        pass


class EapAuthentication(Authentication):
    eap_id = models.CharField(max_length=50)

    def dict(self):
        auth = super(EapAuthentication, self).dict()
        values = auth[self.name]
        values['eap_id'] = self.eap_id
        return auth


class CertificateAuthentication(Authentication):
    identity = models.ForeignKey(AbstractIdentity, null=True, blank=True, default=None, related_name='cert_identity')

    def dict(self):
        auth = super(CertificateAuthentication, self).dict()
        values = auth[self.name]
        ident = self.identity.subclass()
        if not isinstance(ident, DnIdentity):
            values['id'] = ident.value()
        values['certs'].append(self.identity.subclass().certificate.der_container)
        return auth

    def has_private_key(self):
        return self.identity.subclass().certificate.subclass().has_private_key

    def get_key_dict(self):
        key = self.identity.subclass().certificate.subclass().private_key
        return OrderedDict(type=str(key.algorithm).upper(), data=key.der_container)


class EapTlsAuthentication(Authentication):
    eap_id = models.CharField(max_length=50)
    identity = models.ForeignKey(AbstractIdentity, null=True, blank=True, default=None, related_name='tls_identity')

    def dict(self):
        auth = super(EapTlsAuthentication, self).dict()
        values = auth[self.name]
        values['certs'].append(self.identity.subclass().certificate.der_container)
        ident = self.identity.subclass()
        if not isinstance(ident, DnIdentity):
            values['id'] = ident.value()
        values['eap_id'] = self.eap_id
        return auth

    def has_private_key(self):
        return self.identity.subclass().certificate.subclass().has_private_key

    def get_key_dict(self):
        key = self.identity.subclass().certificate.subclass().private_key
        return OrderedDict(type=str(key.algorithm).upper(), data=key.der_container)


class Secret(models.Model):
    type = models.CharField(max_length=50)
    data = fields.EncryptedCharField(max_length=50)
    authentication = models.ForeignKey(Authentication, null=True, blank=True, default=None, related_name='authentication')

    def dict(self):
        eap_id = self.authentication.subclass().eap_id
        secrets = OrderedDict(type=self.type, data=self.data, id=eap_id)
        return secrets


class LogMessage(models.Model):
    connection = models.ForeignKey(Connection, null=True, blank=True, default=None)
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=2)
    message = models.CharField(max_length=50)



