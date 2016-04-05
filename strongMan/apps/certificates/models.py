from enum import Enum

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .container_reader import X509Reader


class DjangoEnum(Enum):
    @classmethod
    def choices(cls):
        # This method converts a Python enum to Django Choises used in the database models
        return [(x.value, x.name) for x in cls]


class KeyContainer(models.Model):
    id = models.AutoField(primary_key=True)
    der_container = models.BinaryField()
    type = models.CharField(max_length=10)
    algorithm = models.CharField(max_length=3)
    public_key_hash = models.TextField()

    class Meta:
        abstract = True

    @classmethod
    def by_bytes(cls, container_bytes, password=None):
        raise NotImplementedError()

    @classmethod
    def by_reader(cls, reader):
        raise NotImplementedError()


class PrivateKey(KeyContainer):
    @classmethod
    def by_reader(cls, reader):
        key = cls()
        key.algorithm = reader.algorithm()
        key.der_container = reader.der_dump()
        key.type = reader.type.value
        key.public_key_hash = reader.public_key_hash()
        key.save()
        return key

    def already_exists(self):
        keys = PrivateKey.objects.filter(public_key_hash=self.public_key_hash)
        count = len(keys)
        return count > 0

    def certificate_exists(self):
        certs = UserCertificate.objects.filter(public_key_hash=self.public_key_hash)
        exists = len(certs) > 0
        return exists

    def connect_to_certificates(self):
        certs = UserCertificate.objects.filter(public_key_hash=self.public_key_hash)
        for cert in certs:
            if cert.private_key is None:
                cert.private_key = self
                cert.save()

    def get_existing_privatekey(self):
        '''
        :returns the private key with the same public key hash
        '''
        assert self.already_exists()
        keys = PrivateKey.objects.filter(public_key_hash=self.public_key_hash)
        return keys[0]


class DistinguishedName(models.Model):
    blob = models.BinaryField()
    location = models.TextField()
    country = models.TextField()
    email = models.TextField()
    organization = models.TextField()
    unit = models.TextField()
    cname = models.TextField()
    province = models.TextField()

    def __str__(self):
        return "C=" + self.country + ", L=" + self.location + ", ST=" + self.province + \
               ", O=" + self.organization + ", OU=" + self.unit + ", CN=" + self.cname


class Certificate(KeyContainer):
    serial_number = models.TextField()
    hash_algorithm = models.CharField(max_length=20)
    is_CA = models.BooleanField()
    valid_not_after = models.DateTimeField()
    valid_not_before = models.DateTimeField()
    issuer = models.OneToOneField(DistinguishedName, on_delete=models.SET_NULL, related_name="issuer", null=True)
    subject = models.OneToOneField(DistinguishedName, on_delete=models.SET_NULL, related_name="subject", null=True)

    def all_identities(self):
        return AbstractIdentity.all_identities(cert_id=self.id)


@receiver(pre_delete, sender=Certificate)
def certificate_clean_submodels(sender, **kwargs):
    '''
    This function gets raised when a certificate gets deleted.
    It assures that all submodels are going to be deleted correctly.
    :return: Nothing
    '''
    cert = kwargs['instance']
    cert.subject.delete()
    cert.issuer.delete()
    # cert.valid_domains.all().delete()


class UserCertificate(Certificate):
    private_key = models.ForeignKey(PrivateKey, null=True, on_delete=models.SET_NULL, related_name="certificates")

    def set_privatekey_if_exists(self):
        """
        Searches for a private key with the same public key
        :return: PrivateKey or None if nothing was found
        """
        keys = PrivateKey.objects.filter(public_key_hash=self.public_key_hash)
        if len(keys) == 1:
            self.private_key = keys[0]

    def already_exists(self):
        keys = UserCertificate.objects.filter(public_key_hash=self.public_key_hash, serial_number=self.serial_number)
        count = len(keys)
        return count > 0

    def remove_privatekey(self):
        privatekey = self.private_key
        self.private_key = None
        self.save()
        if privatekey.certificates.all().__len__() == 0:
            privatekey.delete()


@receiver(pre_delete, sender=UserCertificate)
def usercertificate_clean_submodels(sender, **kwargs):
    cert = kwargs['instance']
    if cert.private_key is not None:
        key = cert.private_key
        cert.private_key = None
        cert.save()
        certs_count_to_privatekey = key.certificates.count()
        no_more_certs_associated = certs_count_to_privatekey == 0
        if no_more_certs_associated:
            key.delete()


class ViciCertificate(Certificate):
    has_private_key = models.BooleanField(default=False)


class CertificateFactory:
    @classmethod
    def distinguishedName_factory(cls, asn1_object):
        dict = asn1_object.native

        subject = DistinguishedName()
        subject.blob = asn1_object.contents
        subject.location = cls._try_to_get_value(dict, ["locality_name"], default="")
        subject.cname = cls._try_to_get_value(dict, ["common_name"], default="")
        subject.country = cls._try_to_get_value(dict, ["country_name"], default="")
        subject.email = cls._try_to_get_value(dict, ["email_address"], default="")
        subject.organization = cls._try_to_get_value(dict, ["organization_name"], default="")
        subject.unit = cls._try_to_get_value(dict, ["organizational_unit_name"], default="")
        subject.province = cls._try_to_get_value(dict, ["state_or_province_name"], default="")
        subject.save()
        return subject

    @classmethod
    def _try_to_get_value(cls, dict, key_path=[], default=None):
        try:
            temp_dict = dict
            for key in key_path:
                temp_dict = temp_dict[key]

            return temp_dict
        except:
            return default

    @classmethod
    def _by_X509Container(cls, reader, certificate_class=UserCertificate):
        public = certificate_class()
        try:
            public.der_container = reader.der_dump()
            public.type = reader.type.value
            public.algorithm = reader.algorithm()
            public.hash_algorithm = reader.asn1.hash_algo
            public.public_key_hash = reader.public_key_hash()
            public.serial_number = reader.asn1.serial_number
            if reader.asn1.ca == None or reader.asn1.ca == False:
                public.is_CA = False
            else:
                public.is_CA = True
            public.valid_not_after = cls._try_to_get_value(reader.asn1.native,
                                                           ["tbs_certificate", "validity", "not_after"])
            public.valid_not_before = cls._try_to_get_value(reader.asn1.native,
                                                            ["tbs_certificate", "validity", "not_before"])
            public.save()
            public.issuer = cls.distinguishedName_factory(reader.asn1.issuer)
            public.subject = cls.distinguishedName_factory(reader.asn1.subject)
            try:
                for san in cls.extract_subject_alt_names(reader):
                    TextIdentity.by_san(san, public)
            except CertificateException as e:
                pass  # No subject_alt_name extension found

            DnIdentity.by_cert(public)

            public.save()
            return public
        except Exception as e:
            if not public.issuer == None:
                public.issuer.delete()
            if not public.subject == None:
                public.subject.delete()
            public.identities.delete()
            public.delete()
            raise e

    @classmethod
    def extract_subject_alt_names(cls, x509reader):
        extensions = x509reader.asn1["tbs_certificate"]["extensions"]
        for extension in extensions:
            name = extension.native["extn_id"]
            if name == "subject_alt_name":
                values = extension.native["extn_value"]
                return values
        raise CertificateException("No subjet_alt_name extension found.")

    @classmethod
    def user_certificate_by_x509reader(cls, reader):
        return cls._by_X509Container(reader, certificate_class=UserCertificate)

    @classmethod
    def vicicertificate_by_dict(cls, cert_dict):
        assert cert_dict['type'] == b'X509'
        reader = X509Reader.by_bytes(cert_dict['data'])
        reader.parse()
        vicicert = cls._by_X509Container(reader, certificate_class=ViciCertificate)
        vicicert.has_private_key = 'has_privkey' in cert_dict and cert_dict['has_privkey'] == b'yes'
        vicicert.save()
        return vicicert


class AbstractIdentity(models.Model):
    '''
    https://wiki.strongswan.org/projects/strongswan/wiki/IdentityParsing
    '''
    certificate = models.ForeignKey(Certificate, null=True, related_name='identities', on_delete=models.CASCADE)

    def __str__(self):
        return str(super(AbstractIdentity, self))

    def value(self):
        raise NotImplementedError()

    @classmethod
    def get_all_subclasses(cls):
        all_subclasses = []

        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(subclass.get_all_subclasses())

        return all_subclasses

    @classmethod
    def all_identities(cls, cert_id=None):
        if cert_id is None:
            ids = [identity.id for identity in AbstractIdentity.objects.all()]
        else:
            ids = [identity.id for identity in AbstractIdentity.objects.filter(certificate_id=cert_id)]
        all_idents = []
        for subclass in AbstractIdentity.get_all_subclasses():
            idents = list(subclass.objects.filter(pk__in=ids))
            all_idents += idents

        return all_idents


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
    '''
    https://tools.ietf.org/html/rfc5280#section-4.2.1.6
    '''

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


class Identity(models.Model):
    pass


class CertificateException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
