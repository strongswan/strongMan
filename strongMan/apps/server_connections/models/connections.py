import json
import sys
from collections.abc import Iterable
from collections import OrderedDict

from django.db import models
from django.db.models import PROTECT
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from strongMan.apps.server_connections.models.common import State
from strongMan.apps.pools.models import Pool
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper

from .specific import Child, Address, Proposal, LogMessage
from .authentication import Authentication, AutoCaAuthentication
from strongMan.apps.certificates.models.certificates import Certificate


class Connection(models.Model):
    VERSION_CHOICES = (
        ('0', "Any IKE version"),
        ('1', "IKEv1"),
        ('2', "IKEv2"),
    )

    profile = models.TextField(unique=True)
    version = models.CharField(max_length=1, choices=VERSION_CHOICES, default=None)
    pool = models.ForeignKey(Pool, null=True, blank=True, default=None, related_name='server_pool',
                             on_delete=PROTECT)
    send_certreq = models.BooleanField(null=True, blank=True, default=None)
    enabled = models.BooleanField(default=False)
    connection_type = models.TextField()
    initiate = models.BooleanField(null=True, blank=True, default=None)

    def dict(self):
        children = OrderedDict()
        for child in self.server_children.all():
            children[child.name] = child.dict()

        ike_sa = OrderedDict()
        if self.pool is not None:
            ike_sa['pools'] = [self.pool.poolname]
        local_address = [local_address.value for local_address in self.server_local_addresses.all()]
        if local_address[0] != '':
            ike_sa['local_addrs'] = local_address
        remote_address = [remote_address.value for remote_address in self.server_remote_addresses.all()]
        if remote_address[0] != '':
            ike_sa['remote_addrs'] = remote_address
        ike_sa['version'] = self.version
        ike_sa['proposals'] = [proposal.type for proposal in self.server_proposals.all()]
        ike_sa['children'] = children
        if self.send_certreq == '1':
            ike_sa['send_certreq'] = 'yes'
        else:
            ike_sa['send_certreq'] = 'no'

        for local in self.server_local.all():
            local = local.subclass()
            ike_sa.update(local.dict())

        for remote in self.server_remote.all():
            remote = remote.subclass()
            ike_sa.update(remote.dict())

        connection = OrderedDict()
        connection[self.profile] = ike_sa
        return connection

    def load(self):
        self.enabled = True
        self.save()
        vici_wrapper = ViciWrapper()
        vici_wrapper.unload_connection(self.profile)
        connection_dict = self.subclass().dict()
        vici_wrapper.load_connection(connection_dict)

        for local in self.server_local.all():
            local = local.subclass()
            if local.has_private_key():
                vici_wrapper.load_key(local.get_key_dict())

        for remote in self.server_remote.all():
            remote = remote.subclass()
            if remote.has_private_key():
                vici_wrapper.load_key(remote.get_key_dict())

        for cert in Certificate.objects.all():
            vici_wrapper.load_certificate(OrderedDict(type=cert.type, flag='None', data=cert.der_container))

    def start(self):
        self.load()
        if self.initiate:
            vici_wrapper = ViciWrapper()
            for child in self.server_children.all():
                logs = vici_wrapper.initiate(child.name, self.profile)
                for log in logs:
                    LogMessage(connection=self, message=log['message']).save()

    def unload(self):
        self.enabled = False
        self.save()
        vici_wrapper = ViciWrapper()
        vici_wrapper.unload_connection(self.profile)

    def stop(self):
        self.unload()
        vici_wrapper = ViciWrapper()
        logs = vici_wrapper.terminate_connection(self.profile)
        for log in logs:
            LogMessage(connection=self, message=log['message']).save()

    @classmethod
    def get_types(cls):
        subclasses = [subclass() for subclass in cls.__subclasses__()]
        return [subclass.get_typ() for subclass in subclasses]

    def get_typ(self):
        return type(self).__name__

    def get_connection_type(self):
        if self.is_remote_access():
            return 'Remote Access'
        else:
            return 'Site to Site'

    def is_remote_access(self):
        return self.connection_type == 'remote_access'

    def is_site_to_site(self):
        return self.connection_type == 'site_to_site'

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

    @property
    def state(self):
        vici_wrapper = ViciWrapper()
        if self.is_remote_access() or self.is_site_to_site() and not self.initiate:
            try:
                loaded = vici_wrapper.is_connection_loaded(self.profile)
                if loaded:
                    return State.LOADED.value
                else:
                    return State.UNLOADED.value
            except Exception:
                return State.UNLOADED.value
        else:
            try:
                state = vici_wrapper.get_connection_state(self.profile)
                if state == State.DOWN.value:
                    return State.DOWN.value
                elif state == State.ESTABLISHED.value:
                    return State.ESTABLISHED.value
                elif state == State.CONNECTING.value:
                    return State.CONNECTING.value
            except Exception:
                return State.DOWN.value

    @property
    def has_auto_ca_authentication(self):
        for remote in self.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, AutoCaAuthentication):
                return True
        return False

    def __str__(self):
        connection = self.dict()
        for con_name in connection:
            for key in connection[con_name]:
                if isinstance(connection[con_name][key], Iterable):
                    if 'certs' in connection[con_name][key]:
                        connection[con_name][key].pop('certs', [])
                    if 'cacerts' in connection[con_name][key]:
                        connection[con_name][key].pop('cacerts', [])
        return str(json.dumps(connection, indent=4))

    def __repr__(self):
        return str(self.version)


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

    @receiver(pre_delete, sender=Connection)
    def delete_all_connected_models(sender, instance, **kwargs):
        for child in Child.objects.filter(connection=instance):
            Proposal.objects.filter(child=child).delete()
            Address.objects.filter(local_ts=child).delete()
            Address.objects.filter(remote_ts=child).delete()
            child.delete()
        Proposal.objects.filter(connection=instance).delete()
        Address.objects.filter(local_addresses=instance).delete()
        Address.objects.filter(remote_addresses=instance).delete()

        for local in Authentication.objects.filter(local=instance):
            local.delete()

        for remote in Authentication.objects.filter(remote=instance):
            remote.delete()
