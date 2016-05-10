import sys
from collections import OrderedDict

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from strongMan.apps.connections.models.common import State

from .specific import Child, Address, Proposal, Secret, LogMessage
from .authentication import Authentication
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper


class Connection(models.Model):
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

    def stop(self):
        vici_wrapper = ViciWrapper()
        vici_wrapper.unload_connection(self.profile)
        logs = vici_wrapper.terminate_connection(self.profile)
        for log in logs:
                LogMessage(connection=self, message=log['message'], level=log['level']).save()

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
        vici_wrapper = ViciWrapper()
        state = vici_wrapper.get_connection_state(self.profile)
        if state == State.DOWN.value:
            return State.DOWN.value
        elif state == State.ESTABLISHED.value:
            return State.ESTABLISHED.value
        elif state == State.CONNECTING.value:
            return State.CONNECTING.value


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