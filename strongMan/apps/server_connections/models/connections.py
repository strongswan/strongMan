import json
import sys
from collections import Iterable
from collections import OrderedDict

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from strongMan.apps.server_connections.models.common import State
from strongMan.apps.pools.models import Pool
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper

from .specific import Child, Address, Proposal, LogMessage
from .authentication import Authentication, AutoCaAuthentication


class Connection(models.Model):
    VERSION_CHOICES = (
        ('0', "IKEv1"),
        ('1', "IKEv2"),
        ('2', "Any IKE version"),
    )

    profile = models.TextField(unique=True)
    version = models.CharField(max_length=1, choices=VERSION_CHOICES, default='2')
    pool = models.ForeignKey(Pool, null=True, blank=True, default=None, related_name='server_pool')
    send_cert_req = models.BooleanField(default=False)
    enabled = models.BooleanField(default=False)

    def dict(self):
        children = OrderedDict()
        for child in self.server_children.all():
            children[child.name] = child.dict()

        ike_sa = OrderedDict()
        ike_sa['remote_addrs'] = [remote_address.value for remote_address in self.server_remote_addresses.all()]
        ike_sa['vips'] = [vip.value for vip in self.server_vips.all()]
        ike_sa['version'] = self.version
        ike_sa['proposals'] = [proposal.type for proposal in self.server_proposals.all()]
        ike_sa['children'] = children

        for local in self.server_local.all():
            local = local.subclass()
            ike_sa.update(local.dict())

        for remote in self.server_remote.all():
            remote = remote.subclass()
            ike_sa.update(remote.dict())

        connection = OrderedDict()
        connection[self.profile] = ike_sa
        return connection

    def start(self):
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

        for child in self.server_children.all():
            logs = vici_wrapper.initiate(child.name, self.profile)
            for log in logs:
                LogMessage(connection=self, message=log['message']).save()

    def stop(self):
        self.enabled = False
        self.save()
        vici_wrapper = ViciWrapper()
        vici_wrapper.unload_connection(self.profile)
        logs = vici_wrapper.terminate_connection(self.profile)
        for log in logs:
            LogMessage(connection=self, message=log['message']).save()

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

    @property
    def state(self):
        try:
            vici_wrapper = ViciWrapper()
            state = vici_wrapper.get_connection_state(self.profile)
            if state == State.DOWN.value:
                return State.DOWN.value
            elif state == State.ESTABLISHED.value:
                return State.ESTABLISHED.value
            elif state == State.CONNECTING.value:
                return State.CONNECTING.value
        except:
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
        Address.objects.filter(vips=instance).delete()

        for local in Authentication.objects.filter(local=instance):
            local.delete()

        for remote in Authentication.objects.filter(remote=instance):
            remote.delete()
