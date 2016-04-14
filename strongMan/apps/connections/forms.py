import sys
from django import forms

from strongMan.apps.certificates.models.identities import AbstractIdentity
from ..certificates.models.certificates import UserCertificate
from .models import Address, Authentication, Secret
from .models import IKEv2EAP, IKEv2CertificateEAP, IKEv2Certificate
from django.core.exceptions import ValidationError


class CertificateChoice(forms.ModelChoiceField):
    @property
    def is_certificate_choice(self):
        return True

class IdentityChoiceValue:
    def __init__(self, identity):
        self.identity = identity

    def __str__(self):
        return str(self.identity)

    def type(self):
        return self.identity.type()


class IdentityChoice(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        super(IdentityChoice, self).__init__(*args, **kwargs)
        self._certificate = None

    def validate(self, value):
        not_selected = value == '-1'
        if not_selected:
            raise ValidationError("This field is required.")
        super(IdentityChoice, self).validate(value)

    @property
    def is_identity_choice(self):
        return True

    @property
    def certificate(self):
        return self._certificate

    @certificate.setter
    def certificate(self, value):
        self._certificate = value
        self.choices = IdentityChoice.to_choices(self._certificate.identities.all())

    @classmethod
    def load_identities(cls, form, certificate_field_name, identity_field_name):
        data_source = {}
        if not form.data == {}:
            data_source = form.data
        elif not form.initial == {}:
            data_source = form.initial
        else:
            raise Exception("Initial and data is empty!")
        if not certificate_field_name in data_source:
            return
        cert_id = data_source[certificate_field_name]
        cert = UserCertificate.objects.filter(pk=cert_id).first()
        identity = form.fields[identity_field_name]
        if not identity.certificate == cert and cert is not None:
            identity.certificate = cert


    @classmethod
    def to_choices(cls, identity_queryset):
        choices = [('',"")]
        for ident in identity_queryset:
            subident = ident.subclass()
            choice = (subident.pk, IdentityChoiceValue(subident))
            choices.append(choice)
        return choices




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



class ChooseTypeForm(forms.Form):
    typ = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(ChooseTypeForm, self).__init__(*args, **kwargs)
        self.fields['typ'].choices = ConnectionForm.get_choices()


class Ike2CertificateForm(ConnectionForm):
    certificate = CertificateChoice(queryset=UserCertificate.objects.all(), empty_label="Choose certificate", required=True)
    identity = IdentityChoice(choices=(), initial="", required=True)

    def update_certificates(self):
        IdentityChoice.load_identities(self, "certificate", "identity")

    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        identity = self.cleaned_data['certificate']
        connection = IKEv2Certificate(profile=profile, auth='pubkey', version=2)
        connection.save()
        Address(value=gateway, remote_addresses=connection).save()
        Authentication(name='remote', auth='pubkey', remote=connection, identity=identity).save()
        Authentication(name='local', auth='pubkey', local=connection).save()

    def update_connection(self, pk):
        connection = IKEv2Certificate.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        connection.profile = self.cleaned_data['profile']
        connection.domain = self.cleaned_data['certificate']
        connection.save()

    def fill(self, connection):
        super(Ike2CertificateForm, self).fill(connection)

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
    certificate = forms.ModelChoiceField(queryset=AbstractIdentity.objects.all(), empty_label=None)
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, initial="", widget=forms.PasswordInput)

    def create_connection(self):
        profile = self.cleaned_data['profile']
        gateway = self.cleaned_data['gateway']
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        identity = self.cleaned_data['certificate']
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
        super(Ike2CertificateForm, self).fill(connection)

    def get_model(self):
        return IKEv2CertificateEAP

    def get_choice_name(self):
        return "IKEv2 Certificate + EAP (Username/Password)"
