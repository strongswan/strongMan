from django import forms
from .models import Connection, Address, Authentication, Secret


VPN_TYPES = (('0', "Choose Type"),
             ('1', "IKEv2 Certificate"),
             ('2', "IKEv2 EAP (Username/Password)"),
             ('3', "IKEv2 Certificate + EAP (Username/Password)"),
             ('4', "IKEv2 EAP-TLS (Certificate)"),
             ('5', "IKEv2 EAP-TNC (Username/Password)"))


class ClientBaseForm(forms.Form):
    profile = forms.CharField(max_length=50, initial="")
    gateway = forms.CharField(max_length=50, initial="")


class ChooseTypeForm(forms.Form):
    typ = forms.ChoiceField(choices=VPN_TYPES)


class Ike2CertificateForm(ClientBaseForm):
    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        connection = Connection(profile=profile, auth='pubkey', version=2, typ=1)
        connection.save()
        address = Address(value=gateway, remote_addresses=connection)
        address.save()
        remote = Authentication(name='remote', auth='pubkey', remote=connection)
        local = Authentication(name='local', peer_id=profile, auth='pubkey', local=connection)
        remote.save()
        local.save()

    def update_connection(self, pk):
        connection = Connection.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        connection.profile = self.cleaned_data['profile']
        connection.save()


class Ike2EapForm(ClientBaseForm):
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, initial="", widget=forms.PasswordInput)

    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        connection = Connection(profile=profile, auth='pubkey', version=2, typ=2)
        connection.save()
        address = Address(value=gateway, remote_addresses=connection)
        address.save()
        secret = Secret(type='EAP', data=password, connection=connection)
        secret.save()
        remote = Authentication(name='remote', auth='pubkey', remote=connection)
        local = Authentication(name='local', peer_id=profile, auth='pubkey', local=connection)
        remote.save()
        local.save()

    def update_connection(self, pk):
        connection = Connection.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        Secret.objects.filter(connection=connection).update(data=self.cleaned_data['password'])
        connection.profile = self.cleaned_data['profile']
        connection.save()


