import sys

from django import forms

from strongMan.apps.certificates.models import UserCertificate, AbstractIdentity
from strongMan.apps.connections.forms.core import CertificateChoice, IdentityChoice
from strongMan.apps.connections.models import IKEv2Certificate, Address, Authentication, IKEv2EAP, Secret, \
    IKEv2CertificateEAP


class ChooseTypeForm(forms.Form):
    form_name = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(ChooseTypeForm, self).__init__(*args, **kwargs)
        self.fields['form_name'].choices = ConnectionForm.get_choices()


class ConnectionForm(forms.Form):
    profile = forms.CharField(max_length=50, initial="")
    gateway = forms.CharField(max_length=50, initial="")

    def fill(self, connection):
        self.fields['profile'].initial = connection.profile
        self.fields['gateway'].initial = connection.remote_addresses.first().value

    def create_connection(self):
        raise NotImplementedError

    def update_connection(self):
        raise NotImplementedError

    def get_model(self):
        raise NotImplementedError

    def get_choice_name(self):
        raise NotImplementedError

    def subclass(self, connection):
        typ = type(connection)
        print(typ)
        for model, form_name in self.get_models():
            if model == typ:
                form_class = getattr(sys.modules[__name__], form_name)
                return form_class()

    def update_certificates(self):
        '''
        This methos is called when a certificate field changed and the identites have to be refreshed
        :return: None
        '''
        pass

    @classmethod
    def get_choices(cls):
        return tuple(
            tuple((type(subclass()).__name__, subclass().get_choice_name())) for subclass in cls.__subclasses__())

    @classmethod
    def get_models(cls):
        return tuple(tuple((subclass().get_model(), type(subclass()).__name__)) for subclass in cls.__subclasses__())


class Ike2CertificateForm(ConnectionForm):
    certificate = CertificateChoice(queryset=UserCertificate.objects.all(), empty_label="Choose certificate",
                                    required=True)
    identity = IdentityChoice(choices=(), initial="", required=True)

    def update_certificates(self):
        IdentityChoice.load_identities(self, "certificate", "identity")

    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        identity_id = self.cleaned_data["identity"]
        identity = AbstractIdentity.objects.get(pk=identity_id)
        connection = IKEv2Certificate(profile=profile, auth='pubkey', version=2)
        connection.save()
        Address(value=gateway, remote_addresses=connection).save()
        Authentication(name='remote', auth='pubkey', remote=connection, identity=identity).save()
        Authentication(name='local', auth='pubkey', local=connection).save()

    def update_connection(self, pk):
        connection = IKEv2Certificate.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        connection.profile = self.cleaned_data['profile']
        remote = connection.remote.first()
        remote.identity = AbstractIdentity.objects.get(pk=self.cleaned_data['identity'])
        remote.save()
        connection.save()

    def fill(self, connection):
        super(Ike2CertificateForm, self).fill(connection)
        self.initial['certificate'] = connection.remote.first().identity.certificate.pk
        self.initial['identity'] = connection.remote.first().identity.pk
        self.update_certificates()

    def get_choice_name(self):
        return "IKEv2 Certificate"

    def get_model(self):
        return IKEv2Certificate


class Ike2EapForm(ConnectionForm):
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, initial="", widget=forms.PasswordInput)

    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        connection = IKEv2EAP(profile=profile, auth='pubkey', version=2)
        connection.save()
        Address(value=gateway, remote_addresses=connection).save()
        Secret(type='EAP', data=password, connection=connection).save()
        Authentication(name='remote', auth='pubkey', remote=connection).save()
        Authentication(name='local', auth='pubkey', local=connection).save()

    def update_connection(self, pk):
        connection = IKEv2EAP.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        Secret.objects.filter(connection=connection).update(data=self.cleaned_data['password'])
        connection.profile = self.cleaned_data['profile']
        connection.save()

    def fill(self, connection):
        super(Ike2EapForm, self).fill(connection)

    def get_choice_name(self):
        return "IKEv2 EAP (Username/Password)"

    def get_model(self):
        return IKEv2EAP


class Ike2EapCertificateForm(ConnectionForm):
    certificate = CertificateChoice(queryset=UserCertificate.objects.all(), empty_label="Choose certificate",
                                    required=True)
    identity = IdentityChoice(choices=(), initial="", required=True)
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, initial="", widget=forms.PasswordInput)

    def update_certificates(self):
        IdentityChoice.load_identities(self, "certificate", "identity")

    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        identity_id = self.cleaned_data["identity"]
        identity = AbstractIdentity.objects.get(pk=identity_id)
        connection = IKEv2CertificateEAP(profile=profile, auth='pubkey', version=2)
        connection.save()
        Address(value=gateway, remote_addresses=connection).save()
        Secret(type='EAP', data=password, connection=connection).save()
        Authentication(name='remote', auth='pubkey', remote=connection, identity=identity).save()
        Authentication(name='local', auth='pubkey', local=connection).save()

    def update_connection(self, pk):
        connection = IKEv2CertificateEAP.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        Secret.objects.filter(connection=connection).update(data=self.cleaned_data['password'])
        connection.profile = self.cleaned_data['profile']
        connection.domain = self.cleaned_data['certificate']
        connection.save()

    def fill(self, connection):
        super(Ike2EapCertificateForm, self).fill(connection)
        self.fields['username'].initial = "to implement!"
        self.fields['password'].initial = "to implement!"
        self.initial['certificate'] = connection.remote.first().identity.certificate.pk
        self.initial['identity'] = connection.remote.first().identity.pk
        self.update_certificates()

    def get_model(self):
        return IKEv2CertificateEAP

    def get_choice_name(self):
        return "IKEv2 Certificate + EAP (Username/Password)"