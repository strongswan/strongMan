from django import forms
from .models import Connection, Address, Authentication, Secret, Typ
from strongMan.apps.certificates.models import AbstractIdentity


class ClientBaseForm(forms.Form):
    profile = forms.CharField(max_length=50, initial="")
    gateway = forms.CharField(max_length=50, initial="")


class ChooseTypeForm(forms.Form):
    typ = forms.ModelChoiceField(queryset=Typ.objects.all(), empty_label=None)


class Ike2CertificateForm(ClientBaseForm):
    #Todo
    #certificate = forms.ModelChoiceField(queryset=AbstractIdentity.all_identities(), empty_label=None)

    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        typ = Typ.objects.get(id=1)
        domain = self.cleaned_data['certificate']
        connection = Connection(profile=profile, auth='pubkey', version=2, typ=typ, domain=domain)
        connection.save()
        Address(value=gateway, remote_addresses=connection).save()
        Authentication(name='remote', auth='pubkey', remote=connection).save()
        Authentication(name='local', peer_id=profile, auth='pubkey', local=connection).save()

    def update_connection(self, pk):
        connection = Connection.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        connection.profile = self.cleaned_data['profile']
        connection.domain = self.cleaned_data['certificate']
        connection.save()


class Ike2EapForm(ClientBaseForm):
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, initial="", widget=forms.PasswordInput)

    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        typ = Typ.objects.get(id=2)
        connection = Connection(profile=profile, auth='pubkey', version=2, typ=typ)
        connection.save()
        Address(value=gateway, remote_addresses=connection).save()
        Secret(type='EAP', data=password, connection=connection).save()
        Authentication(name='remote', auth='pubkey', remote=connection).save()
        Authentication(name='local', peer_id=profile, auth='pubkey', local=connection).save()

    def update_connection(self, pk):
        connection = Connection.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        Secret.objects.filter(connection=connection).update(data=self.cleaned_data['password'])
        connection.profile = self.cleaned_data['profile']
        connection.save()


class Ike2EapCertificateForm(ClientBaseForm):
    #Todo
    #certificate = forms.ModelChoiceField(queryset=AbstractIdentity.all_identities(), empty_label=None)
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, initial="", widget=forms.PasswordInput)

    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        typ = Typ.objects.get(id=3)
        domain = self.cleaned_data['certificate']
        connection = Connection(profile=profile, auth='pubkey', version=2, typ=typ, domain=domain)
        connection.save()
        Address(value=gateway, remote_addresses=connection).save()
        Secret(type='EAP', data=password, connection=connection).save()
        Authentication(name='remote', auth='pubkey', remote=connection).save()
        Authentication(name='local', peer_id=profile, auth='pubkey', local=connection).save()

    def update_connection(self, pk):
        connection = Connection.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        Secret.objects.filter(connection=connection).update(data=self.cleaned_data['password'])
        connection.profile = self.cleaned_data['profile']
        connection.domain = self.cleaned_data['certificate']
        connection.save()


