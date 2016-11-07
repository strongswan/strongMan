from django import forms
from strongMan.apps.certificates.models import UserCertificate, AbstractIdentity
from strongMan.apps.server_connections.models import Connection, Child, Address, Proposal, AutoCaAuthentication, \
    CaCertificateAuthentication, CertificateAuthentication, EapAuthentication, Secret, EapTlsAuthentication, \
    IKEv2Certificate, IKEv2CertificateEAP, IKEv2EAP, IKEv2EapTls
from .FormFields import CertificateChoice, IdentityChoice, PoolChoice, SecretChoice
from strongMan.apps.pools.models import Pool
from strongMan.apps.eap_secrets.models import Secret

VERSION_CHOICES = (
    ('0', "IKEv1"),
    ('1', "IKEv2"),
    ('2', "Any IKE version"),
)


class HeaderForm(forms.Form):
    connection_id = forms.IntegerField(required=False)
    profile = forms.CharField(max_length=50, initial="")
    gateway = forms.CharField(max_length=50, initial="")
    version = forms.ChoiceField(widget=forms.RadioSelect(), choices=VERSION_CHOICES, initial='2')
    pool = PoolChoice(queryset=Pool.objects.none(), label="Pools", required=False)
    send_cert_req = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(HeaderForm, self).__init__(*args, **kwargs)
        self.fields['pool'].queryset = Pool.objects.all()

    def clean_profile(self):
        profile = self.cleaned_data['profile']
        id = self.cleaned_data['connection_id']
        if id is not None:
            if Connection.objects.filter(profile=profile).exclude(pk=id).exists():
                raise forms.ValidationError("Connection with same name already exists!")
        elif Connection.objects.filter(profile=profile).exists():
            raise forms.ValidationError("Connection with same name already exists!")
        return profile

    def fill(self, connection):
        self.initial['profile'] = connection.profile
        self.initial['gateway'] = connection.server_remote_addresses.first().value
        self.initial['version'] = connection.version
        self.initial['pool'] = connection.pool
        self.initial['send_cert_req'] = connection.send_cert_req

    def create_connection(self, connection):
        child = Child(name=self.cleaned_data['profile'], connection=connection)
        child.save()
        self._set_proposals(connection, child)
        self._set_addresses(connection, child, self.cleaned_data['gateway'])

    def update_connection(self, connection):
        Child.objects.filter(connection=connection).update(name=self.cleaned_data['profile'])
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        connection.profile = self.cleaned_data['profile']
        connection.version = self.cleaned_data['version']
        connection.pool = self.cleaned_data['pool']
        connection.send_cert_req = self.cleaned_data['send_cert_req']
        connection.save()

    def model(self):
        raise NotImplementedError

    def get_choice_name(self):
        raise NotImplementedError

    @staticmethod
    def _set_proposals(connection, child):
        #Proposal(type="aes128-sha256-modp2048", connection=connection).save()
        Proposal(type="default", connection=connection).save()
        Proposal(type="aes128gcm128-modp2048", child=child).save()
        #Proposal(type="default", child=child).save()

    @staticmethod
    def _set_addresses(connection, child, gateway):
        Address(value=gateway, remote_addresses=connection).save()
        Address(value='localhost', local_addresses=connection).save()
        Address(value='0.0.0.0', vips=connection).save()
        Address(value='::', vips=connection).save()
        Address(value='::/0', remote_ts=child).save()
        Address(value='0.0.0.0/0', remote_ts=child).save()


class CaCertificateForm(forms.Form):
    """
    Manages the ca certificate field.
    Contains a checkbox for 'auto choosing' the ca certificate and a select field for selecting the certificate manually.
    Either the checkbox is checked or the certificate is selected.
    """
    certificate_ca = CertificateChoice(queryset=UserCertificate.objects.none(), label="CA certificate", required=False)
    certificate_ca_auto = forms.BooleanField(initial=True, required=False)

    def __init__(self, *args, **kwargs):
        super(CaCertificateForm, self).__init__(*args, **kwargs)
        self.fields['certificate_ca'].queryset = UserCertificate.objects.all()

    def clean_certificate_ca(self):
        if "certificate_ca_auto" in self.data:
            return ""
        if not "certificate_ca" in self.data:
            raise forms.ValidationError("This field is required!")
        identity_ca = self.data["certificate_ca"]
        if identity_ca == "":
            raise forms.ValidationError("This field is required!")
        else:
            return identity_ca

    @property
    def is_auto_choose(self):
        return self.cleaned_data["certificate_ca_auto"]

    @is_auto_choose.setter
    def is_auto_choose(self, value):
        self.initial['certificate_ca_auto'] = value

    @property
    def chosen_certificate(self):
        pk = self.cleaned_data["certificate_ca"]
        if pk == '':
            return None
        return UserCertificate.objects.get(pk=pk)

    @chosen_certificate.setter
    def chosen_certificate(self, value):
        self.initial['certificate_ca'] = value

    @classmethod
    def ca_certificate_exists(cls):
        exists = UserCertificate.objects.filter(is_CA=True).count() != 0
        return exists

    def fill(self, connection):
        for local in connection.server_local.all():
            sub = local.subclass()
            if isinstance(sub, AutoCaAuthentication):
                self.is_auto_choose = True
                break
            if isinstance(sub, CaCertificateAuthentication):
                self.chosen_certificate = sub.ca_cert.pk
                self.is_auto_choose = False
                break

    def create_connection(self, connection):
        auth = ''
        if isinstance(connection, IKEv2Certificate):
            auth = 'pubkey'
        if isinstance(connection, IKEv2CertificateEAP):
            auth = 'pubkey'
        if isinstance(connection, IKEv2EAP):
            auth = 'pubkey'
        if isinstance(connection, IKEv2EapTls):
                auth = 'eap-tls'  # or 'eap-ttls'
        if self.is_auto_choose:
            AutoCaAuthentication(name='local', auth=auth, local=connection).save()
        else:
            CaCertificateAuthentication(name='local', auth=auth, local=connection,
                                        ca_cert=self.chosen_certificate).save()

    def update_connection(self, connection):
        for local in connection.server_local.all():
            sub = local.subclass()
            if isinstance(sub, CaCertificateAuthentication):
                sub.delete()
            if isinstance(sub, AutoCaAuthentication):
                sub.delete()
        if self.is_auto_choose:
            AutoCaAuthentication(name='local', auth='pubkey', local=connection).save()
        else:
            CaCertificateAuthentication(name='local', auth='pubkey', local=connection,
                                        ca_cert=self.chosen_certificate).save()


class ServerIdentityForm(forms.Form):
    """
    Manages the server identity field.
    Containes a checkbox to take the gateway field as identity and a field to fill a own identity.
    Either the checkbox is checked or a own identity is field in the textbox.
    """
    identity_ca = forms.CharField(max_length=200, label="Server identity", required=False, initial="")
    is_server_identity = forms.BooleanField(initial=True, required=False)

    def clean_identity_ca(self):
        if "is_server_identity" in self.data:
            return ""
        if not "identity_ca" in self.data:
            raise forms.ValidationError("This field is required!", code='invalid')
        ident = self.data["identity_ca"]
        if ident == "":
            raise forms.ValidationError("This field is required!", code='invalid')
        return ident

    @property
    def is_server_identity_checked(self):
        return self.cleaned_data["is_server_identity"]

    @is_server_identity_checked.setter
    def is_server_identity_checked(self, value):
        self.initial["is_server_identity"] = value

    @property
    def ca_identity(self):
        if self.is_server_identity_checked:
            if 'gateway' not in self.cleaned_data:
                raise Exception("No gateway has been found in this form!")
            return self.cleaned_data['gateway']
        else:
            return self.cleaned_data['identity_ca']

    @ca_identity.setter
    def ca_identity(self, value):
        self.initial["identity_ca"] = value

    def fill(self, connection):
        for local in connection.server_local.all():
            sub = local.subclass()
            if isinstance(sub, CaCertificateAuthentication) or isinstance(sub, AutoCaAuthentication):
                is_server_identity_checked = sub.ca_identity == connection.server_remote_addresses.first().value
                self.is_server_identity_checked = is_server_identity_checked
                if not is_server_identity_checked:
                    self.ca_identity = sub.ca_identity

    def create_connection(self, connection):
        for local in connection.server_local.all():
            sub = local.subclass()
            if isinstance(sub, AutoCaAuthentication) or isinstance(sub, CaCertificateAuthentication):
                sub.ca_identity = self.ca_identity
                sub.save()
                return
        raise Exception(
            "No AutoCaAuthentication or CaCertificateAuthentication found that can be used to insert identity.")

    def update_connection(self, connection):
        for local in connection.server_local.all():
            sub = local.subclass()
            if isinstance(sub, CaCertificateAuthentication) or isinstance(sub, AutoCaAuthentication):
                sub.ca_identity = self.ca_identity
                sub.save()


class UserCertificateForm(forms.Form):
    """
    Form to choose the Usercertifite. Only shows the certs which contains a private key
    """
    certificate = CertificateChoice(queryset=UserCertificate.objects.none(), label="User certificate",
                                    required=True)
    identity = IdentityChoice(choices=(), required=True)

    def __init__(self, *args, **kwargs):
        super(UserCertificateForm, self).__init__(*args, **kwargs)
        self.fields['certificate'].queryset = UserCertificate.objects.filter(private_key__isnull=False)

    def update_certificates(self):
        IdentityChoice.load_identities(self, "certificate", "identity")

    @property
    def my_certificate(self):
        return UserCertificate.objects.get(pk=self.cleaned_data["certificate"])

    @my_certificate.setter
    def my_certificate(self, value):
        self.initial['certificate'] = value
        IdentityChoice.load_identities(self, "certificate", "identity")

    @property
    def my_identity(self):
        return AbstractIdentity.objects.get(pk=self.cleaned_data["identity"])

    @my_identity.setter
    def my_identity(self, value):
        self.initial['identity'] = value

    def fill(self, connection):
        remote_auth = None
        for remote in connection.server_remote.all():
            subclass = remote.subclass()
            if isinstance(subclass, CertificateAuthentication):
                remote_auth = subclass
                break
        if remote_auth is None:
            assert False
        self.my_certificate = remote_auth.identity.certificate.pk
        self.my_identity = remote_auth.identity.pk

    def create_connection(self, connection):
        auth = ''
        if isinstance(connection, IKEv2Certificate):
            auth = 'pubkey'
        if isinstance(connection, IKEv2CertificateEAP):
            auth = 'eap-md5'  # or 'eap-mschapv2|eap-ttls|eap-peap'
        if isinstance(connection, IKEv2EAP):
            auth = 'eap-radius'  # or 'eap-ttls'
        if isinstance(connection, IKEv2EapTls):
            auth = 'eap-tls'  # or 'eap-ttls'
        CertificateAuthentication(name='remote-cert', auth=auth, remote=connection, identity=self.my_identity).save()

    def update_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, CertificateAuthentication):
                sub.identity = self.my_identity
                sub.save()


class EapTlsForm(UserCertificateForm):
    def fill(self, connection):
        remote_auth = None
        for remote in connection.server_remote.all():
            subclass = remote.subclass()
            if isinstance(subclass, EapTlsAuthentication):
                remote_auth = subclass
                break
        if remote_auth is None:
            assert False
        self.my_certificate = remote_auth.identity.certificate.pk
        self.my_identity = remote_auth.identity.pk

    def create_connection(self, connection):
        EapTlsAuthentication(name='remote-eap-tls', auth='eap-tls', remote=connection, identity=self.my_identity).save()

    def update_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, EapTlsAuthentication):
                sub.identity = self.my_identity
                sub.save()


class EapForm(forms.Form):
    """
    Form to choose the eap secret.
    """
    secret = SecretChoice(queryset=Secret.objects.none(), label="EAP Secret", required=False)

    def __init__(self, *args, **kwargs):
        super(EapForm, self).__init__(*args, **kwargs)
        self.fields['secret'].queryset = Secret.objects.all()

    def fill(self, connection):
        self.initial['secret'] = connection.pool
        for remote in connection.server_remote.all():
            subclass = remote.subclass()
            if isinstance(subclass, EapAuthentication):
                self.initial['secret'] = subclass.secret

    def create_connection(self, connection):
        max_round = 0
        for remote in connection.server_remote.all():
            if remote.round > max_round:
                max_round = remote.round

        auth = EapAuthentication(name='remote-eap', auth='eap-radius', remote=connection,
                                 secret=self.cleaned_data['secret'], round=max_round + 1)
        auth.save()

    def update_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, EapAuthentication):
                sub.secret = self.cleaned_data['secret']
                sub.save()
