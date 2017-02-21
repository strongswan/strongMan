from django import forms
from strongMan.apps.certificates.models import UserCertificate, AbstractIdentity
from strongMan.apps.connections.models import Connection, Child, Address, Proposal, AutoCaAuthentication, \
    CaCertificateAuthentication, CertificateAuthentication, EapAuthentication, Secret, EapTlsAuthentication
from .FormFields import CertificateChoice, IdentityChoice


class HeaderForm(forms.Form):
    connection_id = forms.IntegerField(required=False)
    profile = forms.CharField(max_length=50, initial="")
    gateway = forms.CharField(max_length=50, initial="")

    def clean_profile(self):
        profile = self.cleaned_data['profile']
        conn = self.cleaned_data['connection_id']
        if conn is not None:
            if Connection.objects.filter(profile=profile).exclude(pk=conn).exists():
                raise forms.ValidationError("Connection with same name already exists!")
        elif Connection.objects.filter(profile=profile).exists():
            raise forms.ValidationError("Connection with same name already exists!")
        return profile

    def fill(self, connection):
        self.initial['profile'] = connection.profile
        self.initial['gateway'] = connection.remote_addresses.first().value

    def create_connection(self, connection):
        child = Child(name=self.cleaned_data['profile'], connection=connection)
        child.save()
        self._set_proposals(connection, child)
        self._set_addresses(connection, child, self.cleaned_data['gateway'])

    def update_connection(self, connection):
        Child.objects.filter(connection=connection).update(name=self.cleaned_data['profile'])
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['gateway'])
        connection.profile = self.cleaned_data['profile']
        connection.save()

    def model(self):
        raise NotImplementedError

    def get_choice_name(self):
        raise NotImplementedError

    @staticmethod
    def _set_proposals(connection, child):
        Proposal(type="default", connection=connection).save()
        Proposal(type="aes128gcm128-modp2048", child=child).save()

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
    Contains a checkbox for 'auto choosing' the ca certificate and a select field for selecting the
    certificate manually.
    Either the checkbox is checked or the certificate is selected.
    """
    certificate_ca = CertificateChoice(queryset=UserCertificate.objects.none(), label="CA certificate",
                                       required=False)
    certificate_ca_auto = forms.BooleanField(initial=True, required=False)

    def __init__(self, *args, **kwargs):
        super(CaCertificateForm, self).__init__(*args, **kwargs)
        self.fields['certificate_ca'].queryset = UserCertificate.objects.all()

    def clean_certificate_ca(self):
        if "certificate_ca_auto" in self.data:
            return ""
        if "certificate_ca" not in self.data:
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
        for remote in connection.remote.all():
            sub = remote.subclass()
            if isinstance(sub, AutoCaAuthentication):
                self.is_auto_choose = True
                break
            if isinstance(sub, CaCertificateAuthentication):
                self.chosen_certificate = sub.ca_cert.pk
                self.is_auto_choose = False
                break

    def create_connection(self, connection):
        if self.is_auto_choose:
            AutoCaAuthentication(name='remote-cert', auth='pubkey', remote=connection).save()
        else:
            CaCertificateAuthentication(name='remote-cert', auth='pubkey', remote=connection,
                                        ca_cert=self.chosen_certificate).save()

    def update_connection(self, connection):
        for remote in connection.remote.all():
            sub = remote.subclass()
            if isinstance(sub, CaCertificateAuthentication):
                sub.delete()
            if isinstance(sub, AutoCaAuthentication):
                sub.delete()
        if self.is_auto_choose:
            AutoCaAuthentication(name='remote-cert', auth='pubkey', remote=connection).save()
        else:
            CaCertificateAuthentication(name='remote-cert', auth='pubkey', remote=connection,
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
        if "identity_ca" not in self.data:
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
        for remote in connection.remote.all():
            sub = remote.subclass()
            if isinstance(sub, CaCertificateAuthentication) or isinstance(sub, AutoCaAuthentication):
                is_server_identity_checked = sub.ca_identity == connection.remote_addresses.first().value
                self.is_server_identity_checked = is_server_identity_checked
                if not is_server_identity_checked:
                    self.ca_identity = sub.ca_identity

    def create_connection(self, connection):
        for remote in connection.remote.all():
            sub = remote.subclass()
            if isinstance(sub, AutoCaAuthentication) or isinstance(sub, CaCertificateAuthentication):
                sub.ca_identity = self.ca_identity
                sub.save()
                return
        raise Exception("No AutoCaAuthentication or CaCertificateAuthentication found that can be used to "
                        "insert identity.")

    def update_connection(self, connection):
        for remote in connection.remote.all():
            sub = remote.subclass()
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
        local_auth = None
        for local in connection.local.all():
            subclass = local.subclass()
            if isinstance(subclass, CertificateAuthentication):
                local_auth = subclass
                break
        if local_auth is None:
            assert False
        self.my_certificate = local_auth.identity.certificate.pk
        self.my_identity = local_auth.identity.pk

    def create_connection(self, connection):
        CertificateAuthentication(name='local', auth='pubkey', local=connection,
                                  identity=self.my_identity).save()

    def update_connection(self, connection):
        for local in connection.local.all():
            sub = local.subclass()
            if isinstance(sub, CertificateAuthentication):
                sub.identity = self.my_identity
                sub.save()


class EapTlsForm(UserCertificateForm):
    def fill(self, connection):
        local_auth = None
        for local in connection.local.all():
            subclass = local.subclass()
            if isinstance(subclass, EapTlsAuthentication):
                local_auth = subclass
                break
        if local_auth is None:
            assert False
        self.my_certificate = local_auth.identity.certificate.pk
        self.my_identity = local_auth.identity.pk

    def create_connection(self, connection):
        EapTlsAuthentication(name='local-eap-tls', auth='eap-tls', local=connection,
                             identity=self.my_identity).save()

    def update_connection(self, connection):
        for local in connection.local.all():
            sub = local.subclass()
            if isinstance(sub, EapTlsAuthentication):
                sub.identity = self.my_identity
                sub.save()


class EapForm(forms.Form):
    """
    Form to choose the username and password.
    """
    username = forms.CharField(max_length=50, initial="")
    password = forms.CharField(max_length=50, widget=forms.PasswordInput, initial="")

    @property
    def my_username(self):
        return self.cleaned_data["username"]

    @my_username.setter
    def my_username(self, value):
        self.initial['username'] = value

    @property
    def my_password(self):
        return self.cleaned_data["password"]

    @my_password.setter
    def my_password(self, value):
        self.initial['password'] = value

    def fill(self, connection):
        for local in connection.local.all():
            subclass = local.subclass()
            if isinstance(subclass, EapAuthentication):
                self.fields['username'].initial = subclass.eap_id
                self.fields['password'].initial = Secret.objects.filter(authentication=subclass).first().data

    def create_connection(self, connection):
        max_round = 0
        for local in connection.local.all():
            if local.round > max_round:
                max_round = local.round

        auth = EapAuthentication(name='local-eap', auth='eap', local=connection, eap_id=self.my_username,
                                 round=max_round + 1)
        auth.save()
        Secret(type='EAP', data=self.my_password, authentication=auth).save()

    def update_connection(self, connection):
        for local in connection.local.all():
            sub = local.subclass()
            if isinstance(sub, EapAuthentication):
                sub.eap_id = self.my_username
                sub.save()
                Secret.objects.filter(authentication=sub).update(data=self.my_password)
