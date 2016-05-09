import sys

from django import forms

from strongMan.apps.certificates.models import UserCertificate, AbstractIdentity
from strongMan.apps.connections.forms.core import CertificateChoice, IdentityChoice
from strongMan.apps.connections.models import IKEv2Certificate, Address, Authentication, IKEv2EAP, Secret, \
    IKEv2CertificateEAP, Child, EapAuthentication, Proposal, CertificateAuthentication, IKEv2EapTls, \
    EapTlsAuthentication, Connection

class AbstractConForm(forms.Form):
    refresh_choices = forms.CharField(max_length=10, required=False)
    current_form = forms.CharField(max_length=100, required=True)

    @property
    def current_form_class(self):
        current_form_name = self.cleaned_data["current_form"]
        return getattr(sys.modules[__name__], current_form_name)

    @property
    def template(self):
        raise NotImplementedError

    def update_certificates(self):
        '''
        This methos is called when a certificate field changed and the identites have to be refreshed
        :return: None
        '''
        pass

class ChooseTypeForm(AbstractConForm):
    form_name = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(ChooseTypeForm, self).__init__(*args, **kwargs)
        self.fields['form_name'].choices = ConnectionForm.get_choices()

    @property
    def selected_form_class(self):
        name = self.cleaned_data["form_name"]
        return getattr(sys.modules[__name__], name)

    @property
    def template(self):
        return "connections/forms/ChooseType.html"


class ConnectionForm(AbstractConForm):
    connection_id = forms.IntegerField(required=False)
    profile = forms.CharField(max_length=50, initial="")
    gateway = forms.CharField(max_length=50, initial="")
    certificate_ca = CertificateChoice(queryset=UserCertificate.objects.none(), label="CA certificate", required=True)
    identity_ca = forms.CharField(max_length=200, label="Identity", required=False, initial="")
    is_server_identity = forms.BooleanField(initial=True, required=False)

    def clean_identity_ca(self):
        if "is_server_identity" in self.data:
            return ""
        if not "identity_ca" in self.data:
            raise forms.ValidationError("This field is required!")
        identity_ca = self.data["identity_ca"]
        if identity_ca == "":
            raise forms.ValidationError("This field is required!")
        else:
            return identity_ca

    def clean_profile(self):
        profile = self.cleaned_data['profile']
        id = self.cleaned_data['connection_id']
        if id is not None:
            if Connection.objects.filter(profile=profile).exclude(pk=id).exists():
                raise forms.ValidationError("Connection with same name already exists!")
        elif Connection.objects.filter(profile=profile).exists():
            raise forms.ValidationError("Connection with same name already exists!")
        return profile

    def __init__(self, *args, **kwargs):
        super(ConnectionForm, self).__init__(*args, **kwargs)
        self.fields['certificate_ca'].queryset = UserCertificate.objects.all()

    def fill(self, connection):
        self.fields['profile'].initial = connection.profile
        gateway = connection.remote_addresses.first().value
        self.fields['gateway'].initial = gateway
        local = connection.local.first().subclass()
        self.initial['certificate_ca'] = local.ca_cert.pk
        self.initial['identity_ca'] = local.ca_identity
        if local.ca_identity == gateway:
            self.initial["is_server_identity"] = True

    def create_connection(self):
        raise NotImplementedError

    def update_connection(self):
        raise NotImplementedError

    def model(self):
        raise NotImplementedError

    def get_choice_name(self):
        raise NotImplementedError

    def subclass(self, connection):
        typ = type(connection)
        for model, form_name in self.get_models():
            if type(model) == typ:
                form_class = getattr(sys.modules[__name__], form_name)
                return form_class()
        return self

    def update_certificates(self):
        '''
        This method is called when a certificate field changed and the identites have to be refreshed
        :return: None
        '''
        pass

    @property
    def ca_identity(self):
        if self.cleaned_data["is_server_identity"]:
            return self.cleaned_data['gateway']
        else:
            return self.cleaned_data['identity_ca']

    @staticmethod
    def _set_proposals(connection, child):
        Proposal(type="aes128-sha256-modp2048", connection=connection).save()
        Proposal(type="aes128gcm128-modp2048", child=child).save()

    @staticmethod
    def _set_addresses(connection, child, gateway):
        Address(value=gateway, remote_addresses=connection).save()
        Address(value='localhost', local_addresses=connection).save()
        Address(value='0.0.0.0', vips=connection).save()
        Address(value='::', vips=connection).save()
        Address(value='::/0', remote_ts=child).save()
        Address(value='0.0.0.0/0', remote_ts=child).save()

    @classmethod
    def get_choices(cls):
        return tuple(
                tuple((type(subclass()).__name__, subclass().model.choice_name)) for subclass in cls.__subclasses__())

    @classmethod
    def get_models(cls):
        return tuple(tuple((subclass().model(), type(subclass()).__name__)) for subclass in cls.__subclasses__())


class Ike2CertificateForm(ConnectionForm):
    certificate = CertificateChoice(queryset=UserCertificate.objects.none(), label="User certificate",
                                    required=True)
    identity = IdentityChoice(choices=(), required=True)

    def __init__(self, *args, **kwargs):
        super(Ike2CertificateForm, self).__init__(*args, **kwargs)
        self.fields['certificate'].queryset = UserCertificate.objects.filter(private_key__isnull=False)

    def update_certificates(self):
        IdentityChoice.load_identities(self, "certificate", "identity")

    def create_connection(self):
        identity = AbstractIdentity.objects.get(pk=self.cleaned_data["identity"])
        ca_cert = UserCertificate.objects.get(pk=self.cleaned_data["certificate_ca"])
        connection = IKEv2Certificate(profile=self.cleaned_data['profile'], auth='pubkey', version=2)
        connection.save()
        child = Child(name=self.cleaned_data['profile'], connection=connection)
        child.save()
        self._set_proposals(connection, child)
        self._set_addresses(connection, child, self.cleaned_data['gateway'])
        Authentication(name='remote', auth='pubkey', remote=connection).save()

        CertificateAuthentication(name='local', auth='pubkey', local=connection, identity=identity, ca_cert=ca_cert, ca_identity=self.ca_identity).save()

    def update_connection(self, pk):
        connection = IKEv2Certificate.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        connection.profile = self.cleaned_data['profile']
        local = connection.local.first().subclass()
        local.identity = AbstractIdentity.objects.get(pk=self.cleaned_data['identity'])
        local.ca_identity = self.ca_identity
        local.ca_cert = UserCertificate.objects.get(pk=self.cleaned_data["certificate_ca"])
        local.save()
        connection.save()

    def fill(self, connection):
        super(Ike2CertificateForm, self).fill(connection)
        local = connection.local.first().subclass()
        self.initial['certificate'] = local.identity.certificate.pk
        self.initial['identity'] = local.identity.pk
        self.update_certificates()

    @property
    def model(self):
        return IKEv2Certificate

    @property
    def template(self):
        return "connections/forms/Ike2Certificate.html"


class Ike2EapForm(ConnectionForm):
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, widget=forms.PasswordInput, initial="")

    def create_connection(self):
        connection = IKEv2EAP(profile=self.cleaned_data['profile'], auth='pubkey', version=2)
        connection.save()
        child = Child(name=self.cleaned_data['username'], connection=connection)
        child.save()
        self._set_proposals(connection, child)
        self._set_addresses(connection, child, self.cleaned_data['gateway'])
        ca_cert = UserCertificate.objects.get(pk=self.cleaned_data["certificate_ca"])
        Authentication(name='remote-eap', auth='pubkey', remote=connection).save()
        auth = EapAuthentication(name='local-eap', auth='eap', local=connection, eap_id=self.cleaned_data['username'], ca_identity=self.ca_identity, ca_cert=ca_cert)
        auth.save()
        Secret(type='EAP', data=self.cleaned_data['password'], authentication=auth).save()

    def update_connection(self, pk):
        connection = IKEv2EAP.objects.get(id=pk)
        Child.objects.filter(connection=connection).update(name=self.cleaned_data['username'])
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        local = connection.local.first().subclass()
        local.ca_cert = UserCertificate.objects.get(pk=self.cleaned_data["certificate_ca"])
        local.ca_identity = self.ca_identity

        local.eap_id = self.cleaned_data['username']
        local.save()
        connection.profile = self.cleaned_data['profile']
        connection.save()
        Secret.objects.filter(authentication=local).update(data=self.cleaned_data['password'])

    def fill(self, connection):
        super(Ike2EapForm, self).fill(connection)
        local = connection.local.first().subclass()
        self.fields['username'].initial = local.eap_id
        self.fields['password'].initial = Secret.objects.filter(authentication=local).first().data
        self.update_certificates()

    @property
    def model(self):
        return IKEv2EAP

    @property
    def template(self):
        return "connections/forms/Ike2EAP.html"


class Ike2EapCertificateForm(ConnectionForm):
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, initial="")
    certificate = CertificateChoice(queryset=UserCertificate.objects.none(), label="User certificate",
                                    required=True)
    identity = IdentityChoice(choices=(), required=True)

    def __init__(self, *args, **kwargs):
        super(Ike2EapCertificateForm, self).__init__(*args, **kwargs)
        self.fields['certificate'].queryset = UserCertificate.objects.filter(private_key__isnull=False)

    def update_certificates(self):
        IdentityChoice.load_identities(self, "certificate", "identity")

    def create_connection(self):
        identity = AbstractIdentity.objects.get(pk=self.cleaned_data["identity"])
        ca_cert = UserCertificate.objects.get(pk=self.cleaned_data["certificate_ca"])
        connection = IKEv2CertificateEAP(profile=self.cleaned_data['profile'], auth='pubkey', version=2)
        connection.save()
        child = Child(name=self.cleaned_data['username'], connection=connection)
        child.save()
        self._set_proposals(connection, child)
        self._set_addresses(connection, child, self.cleaned_data['gateway'])
        Authentication(name='remote-eap', auth='pubkey', remote=connection).save()
        auth = EapAuthentication(name='local-eap', auth='eap', local=connection, eap_id=self.cleaned_data['username'], round=2, ca_cert=ca_cert, ca_identity=self.ca_identity)
        CertificateAuthentication(name='local-cert', auth='pubkey', local=connection, identity=identity, ca_cert=ca_cert, ca_identity=self.ca_identity).save()
        auth.save()
        Secret(type='EAP', data=self.cleaned_data['password'], authentication=auth).save()

    def update_connection(self, pk):
        connection = IKEv2CertificateEAP.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        connection.profile = self.cleaned_data['profile']
        local_cert = connection.local.filter(name='local-cert').first().subclass()
        local_cert.identity = AbstractIdentity.objects.get(pk=self.cleaned_data['identity'])
        ca_cert = UserCertificate.objects.get(pk=self.cleaned_data["certificate_ca"])
        local_cert.ca_cert = ca_cert
        local_cert.ca_identity = self.ca_identity
        local_cert.save()

        local_eap = connection.local.filter(name='local-eap').first().subclass()
        local_eap.eap_id = self.cleaned_data['username']
        local_eap.ca_identity = self.ca_identity
        local_eap.ca_cert = ca_cert
        local_eap.save()
        Secret.objects.filter(authentication=local_eap).update(data=self.cleaned_data['password'])
        connection.save()

    def fill(self, connection):
        super(Ike2EapCertificateForm, self).fill(connection)
        local_eap = connection.local.filter(name='local-eap').first().subclass()
        self.fields['username'].initial = EapAuthentication.objects.filter(local=connection).first().eap_id
        self.fields['password'].initial = Secret.objects.filter(authentication=local_eap).first().data
        local_cert = connection.local.filter(name='local-cert').first().subclass()
        self.initial['certificate'] = local_cert.identity.certificate.pk
        self.initial['identity'] = local_cert.identity.pk
        self.update_certificates()

    @property
    def model(self):
        return IKEv2CertificateEAP

    @property
    def template(self):
        return "connections/forms/Ike2EapCertificate.html"


class Ike2EapTlsForm(ConnectionForm):
    certificate = CertificateChoice(queryset=UserCertificate.objects.none(), label="User certificate", required=True)
    identity = IdentityChoice(choices=(), initial="", required=True)

    def __init__(self, *args, **kwargs):
        super(Ike2EapTlsForm, self).__init__(*args, **kwargs)
        self.fields['certificate'].queryset = UserCertificate.objects.filter(private_key__isnull=False)

    def update_certificates(self):
        IdentityChoice.load_identities(self, "certificate", "identity")

    def create_connection(self):
        identity = AbstractIdentity.objects.get(pk=self.cleaned_data["identity"])
        ca_cert = UserCertificate.objects.get(pk=self.cleaned_data["certificate_ca"])
        connection = IKEv2EapTls(profile=self.cleaned_data['profile'], auth='pubkey', version=2)
        connection.save()
        child = Child(name=self.cleaned_data['profile'], connection=connection)
        child.save()
        self._set_proposals(connection, child)
        self._set_addresses(connection, child, self.cleaned_data['gateway'])
        Authentication(name='remote-eap-tls', auth='pubkey', remote=connection).save()
        EapTlsAuthentication(name='local-eap-tls', auth='eap-tls', local=connection, identity=identity, ca_cert=ca_cert, ca_identity=self.ca_identity).save()

    def update_connection(self, pk):
        connection = IKEv2EapTls.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        connection.profile = self.cleaned_data['profile']
        local = connection.local.first().subclass()
        local.identity = AbstractIdentity.objects.get(pk=self.cleaned_data['identity'])
        local.ca_cert = UserCertificate.objects.get(pk=self.cleaned_data["certificate_ca"])
        local.ca_identity = self.ca_identity
        local.save()
        connection.save()

    def fill(self, connection):
        super(Ike2EapTlsForm, self).fill(connection)
        local = connection.local.first().subclass()
        self.initial['certificate'] = local.identity.certificate.pk
        self.initial['identity'] = local.identity.pk
        self.update_certificates()

    @property
    def model(self):
        return IKEv2EapTls

    @property
    def template(self):
        return "connections/forms/Ike2EapTls.html"
