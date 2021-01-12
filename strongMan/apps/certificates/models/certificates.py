from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver, Signal

from strongMan.helper_apps.encryption import fields
from .core import CertificateException, CertificateModel, DjangoAbstractBase
from .identities import TextIdentity, DnIdentity
from ..container_reader import X509Reader


class KeyContainer(CertificateModel, models.Model):
    der_container = fields.EncryptedField()
    type = models.CharField(max_length=10)
    algorithm = models.CharField(max_length=3)
    public_key_hash = models.TextField()

    class Meta(object):
        abstract = True

    @classmethod
    def by_bytes(cls, container_bytes, password=None):
        raise NotImplementedError()

    @classmethod
    def by_reader(cls, reader):
        raise NotImplementedError()

    def get_algorithm_type(self):
        if self.algorithm == 'ec':
            return 'ECDSA'
        elif self.algorithm == 'rsa':
            return 'RSA'
        else:
            raise Exception('Algorithm of key is not supported!')


class PrivateKey(KeyContainer):
    # Arguments: "instance"
    should_prevent_delete_signal = Signal()

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


class DistinguishedName(CertificateModel, models.Model):
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


class Certificate(KeyContainer, DjangoAbstractBase):
    serial_number = models.TextField()
    hash_algorithm = models.CharField(max_length=20)
    is_CA = models.BooleanField()
    valid_not_after = models.DateTimeField()
    valid_not_before = models.DateTimeField()
    issuer = models.OneToOneField(DistinguishedName, on_delete=models.SET_NULL,
                                  related_name="certificate_issuer", null=True)
    subject = models.OneToOneField(DistinguishedName, on_delete=models.SET_NULL,
                                   related_name="certificate_subject", null=True)

    @property
    def identities(self):
        return self.ident_certificates_abstractidentity.all()

    @property
    def nickname(self):
        return self.subject.cname


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
    cert.identities.all().delete()


class UserCertificate(Certificate):
    private_key = models.ForeignKey(PrivateKey, null=True, on_delete=models.SET_NULL,
                                    related_name="certificates")
    _nickname = models.TextField()

    # Arguments: "usercertificate", "private_key"
    should_prevent_delete_signal = Signal()

    def set_privatekey_if_exists(self):
        """
        Searches for a private key with the same public key
        :return: PrivateKey or None if nothing was found
        """
        keys = PrivateKey.objects.filter(public_key_hash=self.public_key_hash)
        if len(keys) == 1:
            self.private_key = keys[0]

    def already_exists(self):
        keys = UserCertificate.objects.filter(public_key_hash=self.public_key_hash,
                                              serial_number=self.serial_number)
        count = len(keys)
        return count > 0

    def remove_privatekey(self):
        PrivateKey.should_prevent_delete_signal.send(PrivateKey, usercertificate=self,
                                                     private_key=self.private_key)
        privatekey = self.private_key
        self.private_key = None
        self.save()
        if privatekey.certificates.all().__len__() == 0:
            privatekey.delete()

    def __str__(self):
        return str(self.subject)

    @property
    def has_private_key(self):
        return self.private_key is not None

    @property
    def nickname(self):
        return self._nickname

    @nickname.setter
    def nickname(self, value):
        self._nickname = value


@receiver(pre_delete, sender=UserCertificate)
def usercertificate_clean_submodels(sender, **kwargs):
    cert = kwargs['instance']
    UserCertificate.should_prevent_delete_signal.send(sender=UserCertificate, instance=cert)

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


class CertificateFactory(object):
    @classmethod
    def distinguishedName_factory(cls, asn1_object):
        dic = asn1_object.native

        subject = DistinguishedName()
        subject.blob = asn1_object.contents
        subject.location = cls._try_to_get_value(dic, ["locality_name"], default="")
        subject.cname = cls._try_to_get_value(dic, ["common_name"], default="")
        subject.country = cls._try_to_get_value(dic, ["country_name"], default="")
        subject.email = cls._try_to_get_value(dic, ["email_address"], default="")
        subject.organization = cls._try_to_get_value(dic, ["organization_name"], default="")
        subject.unit = cls._try_to_get_value(dic, ["organizational_unit_name"], default="")
        subject.province = cls._try_to_get_value(dic, ["state_or_province_name"], default="")
        subject.save()
        return subject

    @classmethod
    def _try_to_get_value(cls, dic, key_path, default=None):
        try:
            temp_dic = dic
            for key in key_path:
                temp_dic = temp_dic[key]

            return temp_dic
        except Exception:
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
            if reader.asn1.ca is None or reader.asn1.ca is False:
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
            DnIdentity.by_cert(public)
            try:
                for san in cls.extract_subject_alt_names(reader):
                    TextIdentity.by_san(san, public)
            except CertificateException:
                pass  # No subject_alt_name extension found

            try:
                public.nickname = public.subject.cname
            except Exception:
                pass
            public.save()
            return public
        except Exception as e:
            if public.issuer is not None:
                public.issuer.delete()
            if public.subject is not None:
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
