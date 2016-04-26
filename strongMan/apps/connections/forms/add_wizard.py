import sys

from django import forms

from strongMan.apps.certificates.models import UserCertificate, AbstractIdentity
from strongMan.apps.connections.forms.core import CertificateChoice, IdentityChoice
from strongMan.apps.connections.models import IKEv2Certificate, Address, Authentication, IKEv2EAP, Secret, \
    IKEv2CertificateEAP, Child, EapAuthentication, Proposal, CertificateAuthentication, IKEv2EapTls, \
    EapTlsAuthentication


class ChooseTypeForm(forms.Form):
    form_name = forms.ChoiceField(label="Type:")

    def __init__(self, *args, **kwargs):
        super(ChooseTypeForm, self).__init__(*args, **kwargs)
        self.fields['form_name'].choices = ConnectionForm.get_choices()


class ConnectionForm(forms.Form):
    profile = forms.CharField(max_length=50, initial="", label="Name",
                              widget=forms.TextInput(attrs={'placeholder': 'Name your connection thus you rerecognize it'}))
    gateway = forms.CharField(max_length=50, initial="", label="Server", widget=forms.TextInput(attrs={'placeholder': 'Hostname or IP'}))

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
        for model, form_name in self.get_models():
            if type(model) == typ:
                form_class = getattr(sys.modules[__name__], form_name)
                return form_class()
        return self

    def update_certificates(self):
        '''
        This methos is called when a certificate field changed and the identites have to be refreshed
        :return: None
        '''
        pass

    def update_certificates(self):
        '''
        This method is called when a certificate field changed and the identites have to be refreshed
        :return: None
        '''
        pass

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
                tuple((type(subclass()).__name__, subclass().get_choice_name)) for subclass in cls.__subclasses__())

    @classmethod
    def get_models(cls):
        return tuple(tuple((subclass().get_model(), type(subclass()).__name__)) for subclass in cls.__subclasses__())


class Ike2CertificateForm(ConnectionForm):
    certificate = CertificateChoice(queryset=UserCertificate.objects.none(), empty_label="Choose certificate",
                                    required=True)
    identity = IdentityChoice(choices=(), initial="", required=True)
    certificate_ca = CertificateChoice(queryset=UserCertificate.objects.none(), label="CA certificate",
                                       required=True)
    identity_ca = IdentityChoice(choices=(), initial="", label="CA identity", required=True)

    def __init__(self, *args, **kwargs):
        super(Ike2CertificateForm, self).__init__(*args, **kwargs)
        self.fields['certificate'].queryset = UserCertificate.objects.filter(private_key__isnull=False)
        self.fields['certificate_ca'].queryset = UserCertificate.objects.all()

    def update_certificates(self):
        IdentityChoice.load_identities(self, "certificate", "identity")
        IdentityChoice.load_identities(self, "certificate_ca", "identity_ca")

    def create_connection(self):
        identity = AbstractIdentity.objects.get(pk=self.cleaned_data["identity"])
        identity_ca = AbstractIdentity.objects.get(pk=self.cleaned_data["identity_ca"])
        connection = IKEv2Certificate(profile=self.cleaned_data['profile'], auth='pubkey', version=2)
        connection.save()
        child = Child(name=self.cleaned_data['profile'], connection=connection)
        child.save()
        self._set_proposals(connection, child)
        self._set_addresses(connection, child, self.cleaned_data['gateway'])
        Authentication(name='remote', auth='pubkey', remote=connection).save()
        CertificateAuthentication(name='local', auth='pubkey', local=connection, identity=identity, identity_ca=identity_ca).save()

    def update_connection(self, pk):
        connection = IKEv2Certificate.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        connection.profile = self.cleaned_data['profile']
        local = connection.local.first().subclass()
        local.identity = AbstractIdentity.objects.get(pk=self.cleaned_data['identity'])
        local.identity_ca = AbstractIdentity.objects.get(pk=self.cleaned_data['identity_ca'])
        local.save()
        connection.save()

    def fill(self, connection):
        super(Ike2CertificateForm, self).fill(connection)
        self.initial['certificate'] = connection.local.first().subclass().identity.certificate.pk
        self.initial['identity'] = connection.local.first().subclass().identity.pk
        self.initial['certificate_ca'] = connection.local.first().subclass().identity_ca.certificate.pk
        self.initial['identity_ca'] = connection.local.first().subclass().identity_ca.pk
        self.update_certificates()

    @property
    def get_choice_name(self):
        return "IKEv2 Certificate"

    @property
    def get_model(self):
        return IKEv2Certificate


class Ike2EapForm(ConnectionForm):
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, initial="", widget=forms.PasswordInput)
    certificate = CertificateChoice(queryset=UserCertificate.objects.none(), empty_label="Choose ca certificate",
                                    required=True)
    identity = IdentityChoice(choices=(), initial="", required=True)

    def __init__(self, *args, **kwargs):
        super(Ike2EapForm, self).__init__(*args, **kwargs)
        self.fields[
            'certificate'].queryset = UserCertificate.objects.all()  # init queryset, otherwise it's not going to be updated

    def update_certificates(self):
        IdentityChoice.load_identities(self, "certificate", "identity")

    def create_connection(self):
        connection = IKEv2EAP(profile=self.cleaned_data['profile'], auth='pubkey', version=2)
        connection.save()
        child = Child(name=self.cleaned_data['username'], connection=connection)
        child.save()
        self._set_proposals(connection, child)
        self._set_addresses(connection, child, self.cleaned_data['gateway'])
        identity = AbstractIdentity.objects.get(pk=self.cleaned_data["identity"])
        Authentication(name='remote-eap', auth='pubkey', remote=connection).save()
        auth = EapAuthentication(name='local-eap', auth='eap', local=connection, eap_id=self.cleaned_data['username'], identity_ca=identity)
        auth.save()
        Secret(type='EAP', data=self.cleaned_data['password'], authentication=auth).save()

    def update_connection(self, pk):
        connection = IKEv2EAP.objects.get(id=pk)
        Child.objects.filter(connection=connection).update(name=self.cleaned_data['username'])
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        local = connection.local.first().subclass()
        local.identity_ca = AbstractIdentity.objects.get(pk=self.cleaned_data['identity'])
        local.eap_id = self.cleaned_data['username']
        local.save()
        connection.profile = self.cleaned_data['profile']
        connection.save()
        Secret.objects.filter(authentication=local).update(data=self.cleaned_data['password'])

    def fill(self, connection):
        super(Ike2EapForm, self).fill(connection)
        self.fields['username'].initial = connection.local.first().subclass().eap_id
        local = connection.local.first().subclass()
        self.fields['password'].initial = Secret.objects.filter(authentication=local).first().data
        self.initial['certificate'] = connection.local.first().subclass().identity_ca.certificate.pk
        self.initial['identity'] = connection.local.first().subclass().identity_ca.pk
        self.update_certificates()


    @property
    def get_choice_name(self):
        return "IKEv2 EAP (Username/Password)"

    @property
    def get_model(self):
        return IKEv2EAP


class Ike2EapCertificateForm(ConnectionForm):
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, initial="", widget=forms.PasswordInput)
    certificate = CertificateChoice(queryset=UserCertificate.objects.none(), empty_label="Choose certificate",
                                    required=True)
    identity = IdentityChoice(choices=(), initial="", required=True)
    certificate_ca = CertificateChoice(queryset=UserCertificate.objects.none(), label="CA certificate",
                                       required=True)
    identity_ca = IdentityChoice(choices=(), initial="", label="CA identity", required=True)

    def __init__(self, *args, **kwargs):
        super(Ike2EapCertificateForm, self).__init__(*args, **kwargs)
        self.fields['certificate'].queryset = UserCertificate.objects.filter(private_key__isnull=False)
        self.fields['certificate_ca'].queryset = UserCertificate.objects.all()

    def update_certificates(self):
        IdentityChoice.load_identities(self, "certificate", "identity")
        IdentityChoice.load_identities(self, "certificate_ca", "identity_ca")

    def create_connection(self):
        identity = AbstractIdentity.objects.get(pk=self.cleaned_data["identity"])
        identity_ca = AbstractIdentity.objects.get(pk=self.cleaned_data["identity_ca"])
        connection = IKEv2CertificateEAP(profile=self.cleaned_data['profile'], auth='pubkey', version=2)
        connection.save()
        child = Child(name=self.cleaned_data['username'], connection=connection)
        child.save()
        self._set_proposals(connection, child)
        self._set_addresses(connection, child, self.cleaned_data['gateway'])
        Authentication(name='remote-eap', auth='pubkey', remote=connection).save()
        auth = EapAuthentication(name='local-eap', auth='eap', local=connection, eap_id=self.cleaned_data['username'], round=2, identity_ca=identity)
        CertificateAuthentication(name='local-cert', auth='pubkey', local=connection, identity=identity, identity_ca=identity_ca).save()
        auth.save()
        Secret(type='EAP', data=self.cleaned_data['password'], authentication=auth).save()

    def update_connection(self, pk):
        connection = IKEv2CertificateEAP.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        connection.profile = self.cleaned_data['profile']
        local_cert = connection.local.filter(name='local-cert').first().subclass()
        local_cert.identity = AbstractIdentity.objects.get(pk=self.cleaned_data['identity'])
        local_cert.identity_ca = AbstractIdentity.objects.get(pk=self.cleaned_data['identity_ca'])
        local_cert.save()
        local_eap = connection.local.filter(name='local-eap').first().subclass()
        local_eap.eap_id = self.cleaned_data['username']
        local_eap.identity_ca = AbstractIdentity.objects.get(pk=self.cleaned_data['identity_ca'])
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
        self.initial['certificate_ca'] = local_cert.identity_ca.certificate.pk
        self.initial['identity_ca'] = local_cert.identity_ca.pk
        self.update_certificates()

    @property
    def get_model(self):
        return IKEv2CertificateEAP

    @property
    def get_choice_name(self):
        return "IKEv2 Certificate + EAP (Username/Password)"


class Ike2EapTlsForm(ConnectionForm):
    certificate = CertificateChoice(queryset=UserCertificate.objects.none(), empty_label="Choose certificate",
                                    required=True)
    identity = IdentityChoice(choices=(), initial="", required=True)
    certificate_ca = CertificateChoice(queryset=UserCertificate.objects.none(), label="CA certificate",
                                       required=True)
    identity_ca = IdentityChoice(choices=(), initial="", label="CA identity", required=True)

    def __init__(self, *args, **kwargs):
        super(Ike2EapTlsForm, self).__init__(*args, **kwargs)
        self.fields['certificate'].queryset = UserCertificate.objects.filter(private_key__isnull=False)
        self.fields['certificate_ca'].queryset = UserCertificate.objects.all()

    def update_certificates(self):
        IdentityChoice.load_identities(self, "certificate", "identity")
        IdentityChoice.load_identities(self, "certificate_ca", "identity_ca")

    def create_connection(self):
        identity = AbstractIdentity.objects.get(pk=self.cleaned_data["identity"])
        identity_ca = AbstractIdentity.objects.get(pk=self.cleaned_data["identity_ca"])
        connection = IKEv2EapTls(profile=self.cleaned_data['profile'], auth='pubkey', version=2)
        connection.save()
        child = Child(name=self.cleaned_data['profile'], connection=connection)
        child.save()
        self._set_proposals(connection, child)
        self._set_addresses(connection, child, self.cleaned_data['gateway'])
        Authentication(name='remote-eap-tls', auth='pubkey', remote=connection).save()
        EapTlsAuthentication(name='local-eap-tls', auth='eap-tls', local=connection, identity=identity, identity_ca=identity_ca).save()

    def update_connection(self, pk):
        connection = IKEv2EapTls.objects.get(id=pk)
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        connection.profile = self.cleaned_data['profile']
        local = connection.local.first().subclass()
        local.identity = AbstractIdentity.objects.get(pk=self.cleaned_data['identity'])
        local.identity_ca = AbstractIdentity.objects.get(pk=self.cleaned_data['identity_ca'])
        local.save()
        connection.save()

    def fill(self, connection):
        super(Ike2EapTlsForm, self).fill(connection)
        local = connection.local.first().subclass()
        self.initial['certificate'] = connection.local.first().subclass().identity.certificate.pk
        self.initial['identity'] = connection.local.first().subclass().identity.pk
        self.initial['certificate_ca'] = connection.local.first().subclass().identity_ca.certificate.pk
        self.initial['identity_ca'] = connection.local.first().subclass().identity_ca.pk
        self.update_certificates()

    @property
    def get_choice_name(self):
        return "IKEv2 EAP-TLS (Certificate)"

    @property
    def get_model(self):
        return IKEv2EapTls
