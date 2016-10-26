from collections import OrderedDict

from django.db import models
from django.dispatch import receiver

from strongMan.apps.certificates.models import UserCertificate, CertificateDoNotDelete, PrivateKey
from strongMan.helper_apps.encryption import fields
from .authentication import Authentication
from .common import CertConDoNotDeleteMessage, KeyConDoNotDeleteMessage


@receiver(UserCertificate.should_prevent_delete_signal, sender=UserCertificate)
def prevent_cert_delete_if_cert_is_in_use(sender, **kwargs):
    cert = kwargs['instance']
    authentications = [ident.tls_identity for ident in cert.identities] + [ident.cert_identity for ident in
                                                                           cert.identities] + [
                          cert.ca_cert_authentication]

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


class Child(models.Model):
    name = models.TextField()
    mode = models.TextField()
    connection = models.ForeignKey("server_connections.Connection", null=True, blank=True, default=None,
                                   related_name='server_children')

    def dict(self):
        child = OrderedDict()
        child['remote_ts'] = [remote_t.value for remote_t in self.remote_ts.all()]
        child['esp_proposals'] = [esp_proposal.type for esp_proposal in self.esp_proposals.all()]
        return child


class Address(models.Model):
    value = models.TextField()
    local_ts = models.ForeignKey(Child, null=True, blank=True, default=None, related_name='server_local_ts')
    remote_ts = models.ForeignKey(Child, null=True, blank=True, default=None, related_name='remote_ts')
    remote_addresses = models.ForeignKey("server_connections.Connection", null=True, blank=True, default=None,
                                         related_name='server_remote_addresses')
    local_addresses = models.ForeignKey("server_connections.Connection", null=True, blank=True, default=None,
                                        related_name='server_local_addresses')
    vips = models.ForeignKey("server_connections.Connection", null=True, blank=True, default=None, related_name='server_vips')


class Proposal(models.Model):
    type = models.TextField()
    child = models.ForeignKey(Child, null=True, blank=True, default=None, related_name='server_esp_proposals')
    connection = models.ForeignKey("server_connections.Connection", null=True, blank=True, default=None,
                                   related_name='server_proposals')


class Secret(models.Model):
    eap_username = models.TextField()
    type = models.TextField()
    data = fields.EncryptedCharField(max_length=50)
    authentication = models.ForeignKey(Authentication, null=True, blank=True, default=None,
                                       related_name='server_authentication')


    def dict(self):
        secrets = OrderedDict(type=self.type, data=self.data, id=self.eap_username)
        return secrets


class LogMessage(models.Model):
    connection = models.ForeignKey("server_connections.Connection", null=True, blank=True, default=None)
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
