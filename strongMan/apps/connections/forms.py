from django import forms
from .models import Connection, Address, Authentication, Secret
from strongMan.apps.certificates.models import Identity


class ConnectionForm(forms.Form):
    profile = forms.CharField(max_length=50, initial="")
    gateway = forms.CharField(max_length=50, initial="")

    def create_connection(self):
        raise NotImplementedError

    def update_connection(self):
        raise NotImplementedError

    def type_name(self):
        raise NotImplementedError

    @classmethod
    def get_types(cls):
        subclasses = [subclass() for subclass in cls.__subclasses__()]
        return tuple(subclass.type_name(subclass) for subclass in subclasses)


class ChooseTypeForm(forms.Form):
    typ = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(ChooseTypeForm, self).__init__(*args, **kwargs)
        self.fields['typ'].choices = ConnectionForm.get_types()


class Ike2CertificateForm(ConnectionForm):
    certificate = forms.ModelChoiceField(queryset=Identity.objects.all(), empty_label=None)

    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        domain = self.cleaned_data['certificate']
        connection = Connection(profile=profile, auth='pubkey', version=2, domain=domain)
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

    @staticmethod
    def type_name(cls):
        return type(cls).__name__, "IKEv2 Certificate"


class Ike2EapForm(ConnectionForm):
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, initial="", widget=forms.PasswordInput)

    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        connection = Connection(profile=profile, auth='pubkey', version=2)
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

    @staticmethod
    def type_name(cls):
        return type(cls).__name__, "IKEv2 EAP (Username/Password)"


class Ike2EapCertificateForm(ConnectionForm):
    certificate = forms.ModelChoiceField(queryset=Identity.objects.all(), empty_label=None)
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, initial="", widget=forms.PasswordInput)

    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        domain = self.cleaned_data['certificate']
        connection = Connection(profile=profile, auth='pubkey', version=2, domain=domain)
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

    @staticmethod
    def type_name(cls):
        return type(cls).__name__, "IKEv2 Certificate + EAP (Username/Password)"


