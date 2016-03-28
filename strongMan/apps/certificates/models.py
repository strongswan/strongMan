from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class KeyContainer(models.Model):
    id = models.AutoField(primary_key=True)
    der_container = models.BinaryField()
    type = models.CharField(max_length=10)
    algorithm = models.CharField(max_length=3)
    public_key_hash = models.TextField()

    class Meta:
        abstract = True


class PrivateKey(KeyContainer):
    def already_exists(self):
        keys = PrivateKey.objects.filter(public_key_hash=self.public_key_hash)
        count = len(keys)
        return count > 0

    def certificate_exists(self):
        certs = Certificate.objects.filter(public_key_hash=self.public_key_hash)
        exists = len(certs) > 0
        return exists

    def connect_to_certificates(self):
        certs = Certificate.objects.filter(public_key_hash=self.public_key_hash)
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



class SubjectInfo(models.Model):
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
    issuer = models.OneToOneField(SubjectInfo, on_delete=models.SET_NULL, related_name="issuer", null=True)
    subject = models.OneToOneField(SubjectInfo, on_delete=models.SET_NULL, related_name="subject", null=True)
    private_key = models.ForeignKey(PrivateKey, null=True, on_delete=models.SET_NULL, related_name="certificates")

    def save_new(self):
        self._set_privatekey_if_exists()
        self.issuer.save()
        self.subject.save()
        '''
         These two lines aren't useless!
         This sets the connection between the SubjectInfo and the PublicKey
         You can only do this after the subjectinfo is saved!
        '''
        self.issuer = self.issuer
        self.subject = self.subject
        self.save()

        if hasattr(self, "valid_domains_to_add"):
            for domain in self.valid_domains_to_add:
                domain.certificate = self
                domain.save()

    def _set_privatekey_if_exists(self):
        """
        Searches for a private key with the same public key
        :return: PrivateKey or None if nothing was found
        """
        keys = PrivateKey.objects.filter(public_key_hash=self.public_key_hash)
        if len(keys) == 1:
            self.private_key = keys[0]

    def already_exists(self):
        keys = Certificate.objects.filter(public_key_hash=self.public_key_hash, serial_number=self.serial_number)
        count = len(keys)
        return count > 0

    def add_domain(self, domain):
        if not hasattr(self, "valid_domains_to_add"):
            self.valid_domains_to_add = []
        self.valid_domains_to_add.append(domain)


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
    cert.valid_domains.all().delete()
    if cert.private_key is not None:
        certs_count_to_privatekey = cert.private_key.certificates.all().__len__()
        no_more_certs_associated = certs_count_to_privatekey <= 1
        if no_more_certs_associated:
            cert.private_key.delete()


class Domain(models.Model):
    value = models.TextField()
    certificate = models.ForeignKey(Certificate, null=True, related_name='valid_domains', on_delete=models.CASCADE)


class CertificateException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)