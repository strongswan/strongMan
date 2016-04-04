from strongMan.apps.certificates import models
from .container_reader import X509Reader, PKCS1Reader, PKCS8Reader

from strongMan.apps.vici.wrapper.wrapper import ViciWrapper
class AbstractCertificateManager:
    @classmethod
    def _check_if_parsed(cls, reader):
        if not reader.is_parsed():
            raise CertificateManagerException("The Manager only accepts parsed readers.")

    @classmethod
    def _check_instance_of(cls, reader, should_class):
        if not isinstance(reader, should_class):
            if isinstance(should_class, tuple):
                should_classname = ""
                for klasse in should_class:
                    should_classname += klasse.__name__ + ", "
                should_classname = should_classname[:-2]
            else:
                should_classname = should_class.__name__
            raise CertificateManagerException(
                "Can't manage a " + reader.__class__.__name__ + " in this method. Should be " + should_classname)


class UserCertificateManager(AbstractCertificateManager):
    @classmethod
    def add_pkcs1_or_8(cls, reader):
        cls._check_instance_of(reader, (PKCS1Reader, PKCS8Reader))
        cls._check_if_parsed(reader)
        cert_exists = not cls.certificate_by_hash(reader.public_key_hash()) == None
        if not cert_exists:
            raise CertificateManagerException(
                "It exists no certificate for this private key. Add a certificate first.")
        already_exists = not cls.privatekey_by_hash(reader.public_key_hash()) == None
        if already_exists:
            raise CertificateManagerException(
                "Private key already exists.")
        privatekey = models.PrivateKey.by_pkcs1_or_8_reader(reader)
        privatekey.connect_to_certificates()
        return privatekey

    @classmethod
    def add_x509(cls, reader):
        cls._check_instance_of(reader, X509Reader)
        cls._check_if_parsed(reader)
        already_exists = not cls.certificate_by_hashserial(reader.public_key_hash(), reader.serial_number()) == None
        if already_exists:
            raise CertificateManagerException("Certificate " + reader.cname() + " already exists.")
        cert = models.CertificateFactory.user_certificate_by_x509reader(reader)
        cert.set_privatekey_if_exists()
        cert.save()
        return cert

    @classmethod
    def certificate_by_hashserial(cls, publickey_hash, serial_number):
        certs = models.UserCertificate.objects.filter(public_key_hash=publickey_hash, serial_number=serial_number)
        if len(certs) > 0:
            return certs[0]
        else:
            return None

    @classmethod
    def certificate_by_hash(cls, publickey_hash):
        certs = models.UserCertificate.objects.filter(public_key_hash=publickey_hash)
        if len(certs) > 0:
            return certs[0]
        else:
            return None

    @classmethod
    def privatekey_by_hash(cls, publickey_hash):
        keys = models.PrivateKey.objects.filter(public_key_hash=publickey_hash)
        if len(keys) > 0:
            return keys[0]
        else:
            return None


class ViciCertificateManager(AbstractCertificateManager):
    @classmethod
    def reload_certs(cls):
        '''
        Deletes all ViciCertificates, reads the vici interface and save all Certificates there
        :return None
        '''
        models.ViciCertificate.objects.all().delete()
        wrapper = ViciWrapper()
        vici_certs = wrapper.get_certificates()
        for dict in vici_certs:
            cls._add_x509(dict)


    @classmethod
    def _add_x509(cls, vici_dict):
        cert = models.CertificateFactory.vicicertificate_by_dict(vici_dict)
        cert.save()
        return cert




class CertificateManagerException(models.CertificateException):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
