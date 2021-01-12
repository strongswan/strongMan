from django.db import models

from .core import DjangoAbstractBase, CertificateModel


class AbstractIdentity(DjangoAbstractBase, CertificateModel, models.Model):
    certificate = models.ForeignKey('certificates.Certificate', related_name="ident_%(app_label)s_%(class)s",
                                    on_delete=models.CASCADE)

    def __str__(self):
        return str(super(AbstractIdentity, self))

    def value(self):
        raise NotImplementedError()

    def type(self):
        raise NotImplementedError()

    def abstract_identity(self):
        return AbstractIdentity.objects.get(pk=self.pk)


class TextIdentity(AbstractIdentity):
    text = models.TextField(null=False)

    def __str__(self):
        return self.text

    def value(self):
        return self.text

    def type(self):
        return "subjectAltName"

    @classmethod
    def by_san(cls, subjectAltName, certificate):
        ident = cls()
        ident.text = subjectAltName
        ident.certificate = certificate
        ident.save()
        return ident


class DnIdentity(AbstractIdentity):
    # DistinguishedName identity
    def __str__(self):
        return str(self.certificate.subject)

    def value(self):
        return self.certificate.subject.blob

    def type(self):
        return "distinguishedName"

    @classmethod
    def by_cert(cls, certificate):
        ident = cls()
        ident.certificate = certificate
        ident.save()
        return ident
