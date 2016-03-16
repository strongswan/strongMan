from django.db import models

class Certificate:
    pass

class ASN1(models.Model):
    id=models.AutoField(primary_key=True)
    der_container = models.BinaryField()
    type = models.CharField(max_length=10)
    algorithm = models.CharField(max_length=3)
    identifier = models.TextField()

    class Meta:
        abstract = True


class PrivateKey(ASN1):
    def already_exists(self):
        keys = PrivateKey.objects.filter(identifier=self.identifier)
        count = len(keys)
        return count > 0

    def publickey(self):
        keys = PublicKey.objects.filter(identifier=self.identifier)
        count = len(keys)
        assert not count > 1
        if count == 0:
            return None
        else:
            return keys[0]

    def save_new(self, publickey):
        self.save()
        publickey.private_key = self
        publickey.save()


class SubjectInfo(models.Model):
    location = models.TextField()
    country = models.TextField()
    email = models.TextField()
    organization = models.TextField()
    unit = models.TextField()
    cname = models.TextField()
    province = models.TextField()

class PublicKey(ASN1):
    serial_number = models.TextField()
    hash_algorithm = models.CharField(max_length=20)
    is_CA = models.BooleanField()
    valid_not_after = models.DateTimeField()
    valid_not_before = models.DateTimeField()
    issuer = models.OneToOneField(SubjectInfo, on_delete=models.CASCADE, related_name="issuer", null=True)
    subject = models.OneToOneField(SubjectInfo, on_delete=models.CASCADE, related_name="subject", null=True)
    private_key = models.ForeignKey(PrivateKey, null=True)

    def save_new(self):
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

    def already_exists(self):
        keys = PublicKey.objects.filter(identifier=self.identifier)
        count = len(keys)
        return count > 0





