from django import forms
from strongMan.apps.certificates.models import UserCertificate, AbstractIdentity
from strongMan.apps.server_connections.models import Connection, Child, Address, Proposal, \
    AutoCaAuthentication, CaCertificateAuthentication, CertificateAuthentication, EapAuthentication, \
    EapCertificateAuthentication, EapTlsAuthentication, IKEv2Certificate, IKEv2CertificateEAP
from .FormFields import CertificateChoice, IdentityChoice, PoolChoice
from strongMan.apps.pools.models import Pool


class HeaderForm(forms.Form):
    connection_id = forms.IntegerField(required=False)
    profile = forms.CharField(max_length=50, initial="")
    local_addrs = forms.CharField(max_length=50, initial="", required=False)
    remote_addrs = forms.CharField(max_length=50, initial="", required=False)
    version = forms.ChoiceField(widget=forms.RadioSelect(), choices=Connection.VERSION_CHOICES, initial='2')
    send_certreq = forms.BooleanField(initial=True, required=False)
    local_ts = forms.CharField(max_length=50, initial="", required=False)
    remote_ts = forms.CharField(max_length=50, initial="", required=False)
    start_action = forms.ChoiceField(widget=forms.Select(), choices=Child.START_ACTION_CHOICES,
                                     required=False)
    initiate = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(HeaderForm, self).__init__(*args, **kwargs)

    def clean_profile(self):
        profile = self.cleaned_data['profile']
        id = self.cleaned_data['connection_id']
        if id is not None:
            if Connection.objects.filter(profile=profile).exclude(pk=id).exists():
                raise forms.ValidationError("Connection with same name already exists!")
        elif Connection.objects.filter(profile=profile).exists():
            raise forms.ValidationError("Connection with same name already exists!")
        return profile

    def clean_remote_addrs(self):
        remote_addrs = self.cleaned_data['remote_addrs']
        if remote_addrs == '':
            if 'initiate' in self.data:
                raise forms.ValidationError("This field is required.")
        return remote_addrs

    def fill(self, connection):
        self.initial['profile'] = connection.profile
        self.initial['local_addrs'] = connection.server_local_addresses.first().value
        self.initial['remote_addrs'] = connection.server_remote_addresses.first().value
        self.initial['version'] = connection.version
        self.initial['send_certreq'] = connection.send_certreq
        self.initial['local_ts'] = connection.server_children.first().server_local_ts.first().value
        self.initial['remote_ts'] = connection.server_children.first().server_remote_ts.first().value
        self.initial['start_action'] = connection.server_children.first().start_action
        if connection.is_site_to_site():
            self.initial['initiate'] = connection.initiate

    def create_connection(self, connection):
        child = Child(name=self.cleaned_data['profile'], connection=connection,
                      start_action=self.cleaned_data['start_action'])
        child.save()
        self._set_proposals(connection, child)
        self._set_addresses(connection, child, self.cleaned_data['local_addrs'],
                            self.cleaned_data['remote_addrs'], self.cleaned_data['local_ts'],
                            self.cleaned_data['remote_ts'])

    def update_connection(self, connection):
        Child.objects.filter(connection=connection).update(name=self.cleaned_data['profile'],
                                                           start_action=self.cleaned_data['start_action'])
        Address.objects.filter(local_addresses=connection).update(value=self.cleaned_data['local_addrs'])
        Address.objects.filter(remote_addresses=connection).update(value=self.cleaned_data['remote_addrs'])
        Address.objects.filter(local_ts=connection.server_children.first()).update(
                                                                    value=self.cleaned_data['local_ts'])
        Address.objects.filter(remote_ts=connection.server_children.first()).update(
                                                                    value=self.cleaned_data['remote_ts'])
        connection.profile = self.cleaned_data['profile']
        connection.version = self.cleaned_data['version']
        connection.send_certreq = self.cleaned_data["send_certreq"]
        connection.initiate = self.cleaned_data['initiate']
        connection.save()

    def model(self):
        raise NotImplementedError

    def get_choice_name(self):
        raise NotImplementedError

    @staticmethod
    def _set_proposals(connection, child):
        Proposal(type="aes128-sha256-modp2048", connection=connection).save()
        Proposal(type="aes128gcm128-modp2048", child=child).save()

    @staticmethod
    def _set_addresses(connection, child, local_addrs, remote_addrs, local_ts, remote_ts):
        Address(value=local_addrs, local_addresses=connection).save()
        Address(value=remote_addrs, remote_addresses=connection).save()
        Address(value=local_ts, local_ts=child).save()
        Address(value=remote_ts, remote_ts=child).save()


class PoolForm(forms.Form):
    pool = PoolChoice(queryset=Pool.objects.none(), label="Pools", empty_label="Nothing selected",
                      required=False)

    def __init__(self, *args, **kwargs):
        super(PoolForm, self).__init__(*args, **kwargs)
        self.fields['pool'].queryset = Pool.objects.all()

    def fill(self, connection):
        self.initial['pool'] = connection.pool

    def update_connection(self, connection):
        connection.pool = self.cleaned_data['pool']
        connection.save()


class RemoteCertificateForm(forms.Form):
    """
    Manages the remote certificate field.
    Contains a checkbox for 'auto choosing' the ca certificate and a select field for selecting the
    certificate manually.
    Either the checkbox is checked or the certificate is selected.
    """
    certificate_ca = CertificateChoice(queryset=UserCertificate.objects.none(), label="CA/Peer certificate",
                                       empty_label="Nothing selected", required=False)
    certificate_ca_auto = forms.BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):
        super(RemoteCertificateForm, self).__init__(*args, **kwargs)
        self.fields['certificate_ca'].queryset = UserCertificate.objects.all()

    @property
    def is_auto_choose(self):
        return self.cleaned_data["certificate_ca_auto"]

    @is_auto_choose.setter
    def is_auto_choose(self, value):
        self.initial['certificate_ca_auto'] = value

    @property
    def chosen_certificate(self):
        pk = self.cleaned_data["certificate_ca"]
        if pk is None or pk == '':
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
                if sub.ca_cert is not None:
                    self.chosen_certificate = sub.ca_cert.pk
                self.is_auto_choose = False
                self.initial['remote_auth'] = sub.auth
                break

    def create_connection(self, connection):
        if isinstance(connection, IKEv2Certificate) or isinstance(connection, IKEv2CertificateEAP):
            auth = 'pubkey'
        else:
            auth = self.cleaned_data['remote_auth']
        if self.is_auto_choose:
            AutoCaAuthentication(name='remote', auth=auth, remote=connection).save()
        else:
            if self.chosen_certificate is None:
                CaCertificateAuthentication(name='remote', auth=auth, remote=connection).save()
            else:
                CaCertificateAuthentication(name='remote', auth=auth, remote=connection,
                                            ca_cert=self.chosen_certificate).save()

    def update_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, CaCertificateAuthentication):
                sub.delete()
            if isinstance(sub, AutoCaAuthentication):
                sub.delete()
        if isinstance(connection, IKEv2Certificate) or isinstance(connection, IKEv2CertificateEAP):
            auth = 'pubkey'
        else:
            auth = self.cleaned_data['remote_auth']
        if self.is_auto_choose:
            AutoCaAuthentication(name='remote', auth=auth, remote=connection).save()
        else:
            CaCertificateAuthentication(name='remote', auth=auth, remote=connection,
                                        ca_cert=self.chosen_certificate).save()


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

        auth = EapCertificateAuthentication(name='remote-eap', auth=self.cleaned_data['remote_auth'],
                                            remote=connection, round=max_round + 1)
        auth.save()

    def update_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, EapCertificateAuthentication):
                sub.auth = self.cleaned_data['remote_auth']
                sub.save()


class RemoteIdentityForm(forms.Form):
    """
    Manages the remote identity field.
    Containes a checkbox to take the local address field as identity and a field to fill a own identity.
    Either the checkbox is checked or a own identity is field in the textbox.
    """
    identity_ca = forms.CharField(max_length=200, label="Peer identity", required=False, initial="")
    is_server_identity = forms.BooleanField(initial=False, required=False)

    @property
    def is_server_identity_checked(self):
        return self.cleaned_data["is_server_identity"]

    @is_server_identity_checked.setter
    def is_server_identity_checked(self, value):
        self.initial["is_server_identity"] = value

    @property
    def ca_identity(self):
        if self.is_server_identity_checked:
            if 'remote_addrs' not in self.cleaned_data:
                raise Exception("No remote address has been found in this form!")
            return self.cleaned_data['remote_addrs']
        else:
            return self.cleaned_data['identity_ca']

    @ca_identity.setter
    def ca_identity(self, value):
        self.initial["identity_ca"] = value

    def fill(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, CaCertificateAuthentication) or isinstance(sub, AutoCaAuthentication):
                is_checked = sub.ca_identity == connection.server_remote_addresses.first().value
                self.is_server_identity_checked = is_checked
                if is_checked is False:
                    self.ca_identity = sub.ca_identity

    def create_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, AutoCaAuthentication) or isinstance(sub, CaCertificateAuthentication):
                sub.ca_identity = self.ca_identity
                sub.save()
                return
        raise Exception("No AutoCaAuthentication or CaCertificateAuthentication found that can be used to "
                        "insert identity.")

    def update_connection(self, connection):
        for remote in connection.server_remote.all():
            sub = remote.subclass()
            if isinstance(sub, CaCertificateAuthentication) or isinstance(sub, AutoCaAuthentication):
                sub.ca_identity = self.ca_identity
                sub.save()


class ServerCertificateForm(forms.Form):
    """
    Form to choose the server certifite. Only shows the certs which contains a private key
    """
    certificate = CertificateChoice(queryset=UserCertificate.objects.none(), label="Server certificate",
                                    empty_label="Nothing selected", required=True)
    identity = IdentityChoice(choices=(), required=True)

    def __init__(self, *args, **kwargs):
        super(ServerCertificateForm, self).__init__(*args, **kwargs)
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


class EapTlsForm(ServerCertificateForm):
    remote_auth = forms.ChoiceField(widget=forms.Select(), choices=EapTlsAuthentication.AUTH_CHOICES)

    def fill(self, connection):
        local_auth = None
        for local in connection.server_local.all():
            subclass = local.subclass()
            if isinstance(subclass, EapTlsAuthentication):
                local_auth = subclass
                break
        if local_auth is None:
            assert False
        self.my_certificate = local_auth.identity.certificate.pk
        self.my_identity = local_auth.identity.pk
        self.initial['remote_auth'] = local_auth.auth

    def create_connection(self, connection):
        auth = self.cleaned_data['remote_auth']
        EapTlsAuthentication(name='local', auth=auth, local=connection,
                             identity=self.my_identity).save()

    def update_connection(self, connection):
        for local in connection.server_local.all():
            sub = local.subclass()
            if isinstance(sub, EapTlsAuthentication):
                sub.identity = self.my_identity
                sub.auth = self.cleaned_data['remote_auth']
                sub.save()


class EapForm(ServerCertificateForm):
    """
    Form to choose the eap secret.
    """
    remote_auth = forms.ChoiceField(widget=forms.Select(), choices=EapAuthentication.AUTH_CHOICES)

    def __init__(self, *args, **kwargs):
        super(EapForm, self).__init__(*args, **kwargs)

    def fill(self, connection):
        local_auth = None
        for local in connection.server_local.all():
            subclass = local.subclass()
            if isinstance(subclass, EapAuthentication):
                local_auth = subclass
                break
        if local_auth is None:
            assert False
        self.my_certificate = local_auth.identity.certificate.pk
        self.my_identity = local_auth.identity.pk

    def create_connection(self, connection):
        max_round = 0
        for local in connection.server_local.all():
            if local.round > max_round:
                max_round = local.round

        auth = EapAuthentication(name='local', auth='pubkey', local=connection,
                                 round=max_round + 1, identity=self.my_identity)
        auth.save()

    def update_connection(self, connection):
        for local in connection.server_remote.all():
            sub = local.subclass()
            if isinstance(sub, EapAuthentication):
                sub.identity = self.my_identity
                sub.save()
