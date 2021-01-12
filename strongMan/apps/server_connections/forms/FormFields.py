from django import forms
from strongMan.apps.certificates.models import UserCertificate


class CertificateChoice(forms.ModelChoiceField):
    @property
    def is_certificate_choice(self):
        return True


class PoolChoice(forms.ModelChoiceField):
    @property
    def is_pool_choice(self):
        return True


class IdentityChoiceValue(object):
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
            return
        if certificate_field_name not in data_source:
            return
        cert_id = data_source[certificate_field_name]
        if cert_id != "":
            cert = UserCertificate.objects.filter(pk=cert_id).first()
            identity = form.fields[identity_field_name]
            if not identity.certificate == cert and cert is not None:
                identity.certificate = cert

    @classmethod
    def to_choices(cls, identity_queryset):
        choices = []
        for ident in identity_queryset:
            subident = ident.subclass()
            choice = (subident.pk, IdentityChoiceValue(subident))
            choices.append(choice)
        return choices
