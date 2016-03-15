from django.db import models

class Certificate:
    pass

class ASN1(models.Model):
    der_container = models.BinaryField()
    type = models.CharField(max_length=10)
    algorithm = models.CharField(max_length=3)

    class Meta:
        abstract = True


class PrivateKey(ASN1):
    pass


class SubjectInfo(models.Model):
    location = models.TextField()
    country = models.TextField()
    email = models.TextField()
    organization = models.TextField()
    unit = models.TextField()
    cname = models.TextField()
    province = models.TextField()

class PublicKey(ASN1):
    serial_number = models.IntegerField()
    hash_algorithm = models.CharField(max_length=20)
    is_CA = models.BooleanField()
    valid_not_after = models.DateTimeField()
    valid_not_before = models.DateTimeField()
    issuer = models.ForeignKey(SubjectInfo)
    subject = models.ForeignKey(SubjectInfo)
    private_key= models.ForeignKey(PrivateKey)





