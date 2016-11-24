from django import forms
from strongMan.apps.certificates.models import UserCertificate, AbstractIdentity
from strongMan.apps.server_connections.models import Connection, Child, Address, Proposal, AutoCaAuthentication, \
    CaCertificateAuthentication, CertificateAuthentication, EapAuthentication, EapCertificateAuthentication, \
    EapTlsAuthentication, IKEv2CertificateEAP, IKEv2EAP, IKEv2EapTls
from .FormFields import CertificateChoice, IdentityChoice, PoolChoice
from strongMan.apps.pools.models import Pool
from itertools import chain


class HeaderForm(forms.Form):
    connection_id = forms.IntegerField(required=False)
    profile = forms.CharField(max_length=50, initial="")
    local_addrs = forms.CharField(max_length=50, initial="")
    remote_addrs = forms.CharField(max_length=50, initial="", required=False)
    version = forms.ChoiceField(widget=forms.RadioSelect(), choices=Connection.VERSION_CHOICES, initial='2')
    pool = PoolChoice(queryset=Pool.objects.none(), label="Pools", required=False)
    send_cert_req = forms.BooleanField(required=False)
    local_ts = forms.CharField(max_length=50, initial="")
    remote_ts = forms.CharField(max_length=50, initial="")

    def __init__(self, *args, **kwargs):
        super(HeaderForm, self).__init__(*args, **kwargs)
        self.fields['pool'].queryset = chain({'-------------'}, Pool.objects.all())

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
        self.initial['local_addrs'] = connection.server_local_addresses.first().value
        self.initial['remote_addrs'] = connection.server_remote_addresses.first().value
        self.initial['version'] = connection.version
        self.initial['pool'] = connection.pool
        self.initial['send_cert_req'] = connection.send_cert_req
        self.initial['local_ts'] = connection.server_children.first().server_local_ts.first().value
        self.initial['remote_ts'] = connection.server_children.first().server_remote_ts.first().value

    def create_connection(self, connection):
        child = Child(name=self.cleaned_data['profile'], connection=connection)
        child.save()
        self._set_proposals(connection, child)
        self._set_addresses(connection, child, self.cleaned_data['local_addrs'], self.cleaned_data['remote_addrs'],
                            self.cleaned_data['local_ts'], self.cleaned_data['remote_ts'])

    def update_connection(self, connection):
        Child.objects.filter(connection=connection).update(name=self.cleaned_data['profile'])
        Address.objects.filter(local_addresses=connection).update(value=self.cleaned_data['local_addrs'])
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['remote_addrs'])
        Address.objects.filter(local_ts=connection.server_children.first()).update(value=self.cleaned_data['local_ts'])
        Address.objects.filter(remote_ts=connection.server_children.first()).update(value=self.cleaned_data['remote_ts'])
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
        Proposal(type="aes128-sha256-modp2048", connection=connection).save()
        Proposal(type="aes128gcm128-modp2048", child=child).save()
        #Proposal(type="default", child=child).save()

    @staticmethod
    def _set_addresses(connection, child, local_addrs, remote_addrs, local_ts, remote_ts):
        Address(value=local_addrs, local_addresses=connection).save()
        Address(value=remote_addrs, remote_addresses=connection).save()
        Address(value='0.0.0.0', vips=connection).save()
        Address(value='::', vips=connection).save()
        Address(value=local_ts, local_ts=child).save()
        Address(value=remote_ts, remote_ts=child).save()


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
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, AutoCaAuthentication):
                self.is_auto_choose = True
                break
            if isinstance(sub, CaCertificateAuthentication):
                self.chosen_certificate = sub.ca_cert.pk
                self.is_auto_choose = False
                break

    def create_connection(self, connection):
        if isinstance(connection, IKEv2EapTls):
            auth = self.cleaned_data['remote_auth']
        else:
            auth = 'pubkey'
        if self.is_auto_choose:
            AutoCaAuthentication(name='remote-cert', auth=auth, remote=connection).save()
        else:
            CaCertificateAuthentication(name='remote-cert', auth=auth, remote=connection,
                                        ca_cert=self.chosen_certificate).save()

    def update_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, CaCertificateAuthentication):
                sub.delete()
            if isinstance(sub, AutoCaAuthentication):
                sub.delete()
        if isinstance(connection, IKEv2EapTls):
            auth = self.cleaned_data['remote_auth']
        else:
            auth = 'pubkey'
        if self.is_auto_choose:
            AutoCaAuthentication(name='remote-cert', auth=auth, remote=connection).save()
        else:
            CaCertificateAuthentication(name='remote-cert', auth=auth, remote=connection,
                                        ca_cert=self.chosen_certificate).save()


class ServerIdentityForm(forms.Form):
    """
    Manages the server identity field.
    Containes a checkbox to take the local address field as identity and a field to fill a own identity.
    Either the checkbox is checked or a own identity is field in the textbox.
    """
    identity_ca = forms.CharField(max_length=200, label="Server identity", required=False, initial="")
    is_server_identity = forms.BooleanField(initial=False, required=False)

    # def clean_identity_ca(self):
        # if "is_server_identity" in self.data:
        #     return ""
        # if not "identity_ca" in self.data:
        #     raise forms.ValidationError("This field is required!", code='invalid')
        # ident = self.data["identity_ca"]
        # if ident == "":
        #     raise forms.ValidationError("This field is required!", code='invalid')
        # return ident

    @property
    def is_server_identity_checked(self):
        return self.cleaned_data["is_server_identity"]

    @is_server_identity_checked.setter
    def is_server_identity_checked(self, value):
        self.initial["is_server_identity"] = value

    @property
    def ca_identity(self):
        if self.is_server_identity_checked:
            if 'local_addrs' not in self.cleaned_data:
                raise Exception("No local address has been found in this form!")
            return self.cleaned_data['local_addrs']
        else:
            return self.cleaned_data['identity_ca']

    @ca_identity.setter
    def ca_identity(self, value):
        self.initial["identity_ca"] = value

    def fill(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, CaCertificateAuthentication) or isinstance(sub, AutoCaAuthentication):
                if connection.server_remote_addresses.first() is not None:
                    is_server_identity_checked = sub.ca_identity == connection.server_remote_addresses.first().value
                    self.is_server_identity_checked = is_server_identity_checked
                    if not is_server_identity_checked:
                        self.ca_identity = sub.ca_identity

    def create_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, AutoCaAuthentication) or isinstance(sub, CaCertificateAuthentication):
                sub.ca_identity = self.ca_identity
                sub.save()
                return
        raise Exception(
            "No AutoCaAuthentication or CaCertificateAuthentication found that can be used to insert identity.")

    def update_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, CaCertificateAuthentication) or isinstance(sub, AutoCaAuthentication):
                sub.ca_identity = self.ca_identity
                sub.save()


class UserCertificateForm(forms.Form):
    """
    Form to choose the Usercertifite. Only shows the certs which contains a private key
    """
    certificate = CertificateChoice(queryset=UserCertificate.objects.none(), label="Server certificate",
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
        for local in connection.server_local.all():
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
        for local in connection.server_local.all():
            sub = local.subclass()
            if isinstance(sub, CertificateAuthentication):
                sub.identity = self.my_identity
                sub.save()

# class UserCertificateForm(forms.Form):
#     """
#     Form to choose the Usercertifite. Only shows the certs which contains a private key
#     """
#     certificate = CertificateChoice(queryset=UserCertificate.objects.none(), label="User certificate",
#                                     required=True)
#     identity = IdentityChoice(choices=(), required=True)
#
#     def __init__(self, *args, **kwargs):
#         super(UserCertificateForm, self).__init__(*args, **kwargs)
#         self.fields['certificate'].queryset = UserCertificate.objects.filter(private_key__isnull=False)
#
#     def update_certificates(self):
#         IdentityChoice.load_identities(self, "certificate", "identity")
#
#     @property
#     def my_certificate(self):
#         return UserCertificate.objects.get(pk=self.cleaned_data["certificate"])
#
#     @my_certificate.setter
#     def my_certificate(self, value):
#         self.initial['certificate'] = value
#         IdentityChoice.load_identities(self, "certificate", "identity")
#
#     @property
#     def my_identity(self):
#         return AbstractIdentity.objects.get(pk=self.cleaned_data["identity"])
#
#     @my_identity.setter
#     def my_identity(self, value):
#         self.initial['identity'] = value
#
#     def fill(self, connection):
#         remote_auth = None
#         for remote in connection.server_remote.all():
#             subclass = remote.subclass()
#             if isinstance(subclass, CertificateAuthentication):
#                 remote_auth = subclass
#                 break
#         if remote_auth is None:
#             assert False
#         self.my_certificate = remote_auth.identity.certificate.pk
#         self.my_identity = remote_auth.identity.pk
#
#     def create_connection(self, connection):
#         CertificateAuthentication(name='remote-cert', auth='pubkey', remote=connection,
#                                   identity=self.my_identity).save()
#
#     def update_connection(self, connection):
#         for remote in connection.server_remote.all():
#             sub = remote.subclass()
#             if isinstance(sub, CertificateAuthentication):
#                 sub.identity = self.my_identity
#                 sub.save()


class EapTlsForm(UserCertificateForm):
    remote_auth = forms.ChoiceField(widget=forms.Select(), choices=EapTlsAuthentication.AUTH_CHOICES)

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
        self.initial['remote_auth'] = remote_auth.auth

    def create_connection(self, connection):
        EapTlsAuthentication(name='remote-eap-tls', auth=self.cleaned_data['remote_auth'], remote=connection,
                             identity=self.my_identity).save()

    def update_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, EapTlsAuthentication):
                sub.identity = self.my_identity
                sub.auth = self.cleaned_data['remote_auth']
                sub.save()


class EapForm(forms.Form):
    """
    Form to choose the eap secret.
    """
    remote_auth = forms.ChoiceField(widget=forms.Select(), choices=EapAuthentication.AUTH_CHOICES)

    def __init__(self, *args, **kwargs):
        super(EapForm, self).__init__(*args, **kwargs)

    def fill(self, connection):
        remote_auth = None
        for remote in connection.server_remote.all():
            subclass = remote.subclass()
            if isinstance(subclass, EapAuthentication):
                remote_auth = subclass
                break
        if remote_auth is None:
            assert False
        if isinstance(remote_auth, IKEv2EAP):
            self.initial['remote_auth'] = remote_auth.auth
        if isinstance(remote_auth, IKEv2CertificateEAP):
            self.initial['remote_auth'] = remote_auth.auth_certificate

    def create_connection(self, connection):
        max_round = 0
        for remote in connection.server_remote.all():
            if remote.round > max_round:
                max_round = remote.round

        auth = EapAuthentication(name='remote-eap', auth=self.cleaned_data['remote_auth'], remote=connection,
                                 round=max_round + 1)
        auth.save()

    def update_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, EapAuthentication):
                sub.auth = self.cleaned_data['remote_auth']
                sub.save()


class EapCertificateForm(forms.Form):
    """
    Form to choose the eap secret for 2 round authentication.
    """
    remote_auth = forms.ChoiceField(widget=forms.Select(), choices=EapCertificateAuthentication.AUTH_CHOICES)

    def __init__(self, *args, **kwargs):
        super(EapCertificateForm, self).__init__(*args, **kwargs)

    def fill(self, connection):
        remote_auth = None
        for remote in connection.server_remote.all():
            subclass = remote.subclass()
            if isinstance(subclass, EapCertificateAuthentication):
                remote_auth = subclass
                break
        if remote_auth is None:
            assert False
        self.initial['remote_auth'] = remote_auth.auth

    def create_connection(self, connection):
        max_round = 0
        for remote in connection.server_remote.all():
            if remote.round > max_round:
                max_round = remote.round

        auth = EapCertificateAuthentication(name='remote-eap', auth=self.cleaned_data['remote_auth'], remote=connection,
                                            round=max_round + 1)
        auth.save()

    def update_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, EapCertificateAuthentication):
                sub.auth = self.cleaned_data['remote_auth']
                sub.save()