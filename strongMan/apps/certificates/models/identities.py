from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .core import DjangoAbstractBase, CertificateModel


class AbstractIdentity(DjangoAbstractBase, CertificateModel, models.Model):
    # GenericForeignKey:
    # http://voorloopnul.com/blog/using-django-generic-relations/
    certificate_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    certificate_id = models.PositiveIntegerField()
    certificate = GenericForeignKey('certificate_type', 'certificate_id')

    def __str__(self):
        return str(super(AbstractIdentity, self))

    def value(self):
        raise NotImplementedError()


class TextIdentity(AbstractIdentity):
    text = models.TextField(null=False)

    def __str__(self):
        return self.text

    def value(self):
        return self.text

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
        return self.certificate.subject

    @classmethod
    def by_cert(cls, certificate):
        ident = cls()
        ident.certificate = certificate
        ident.save()
        return ident
