import strongMan.apps.certificates.models.certificates
from strongMan.apps.server_connections import models

from strongMan.apps.vici.wrapper.wrapper import ViciWrapper


class UserCertificateManager:
    @classmethod
    def _check_if_parsed(cls, reader):
        if not reader.is_parsed():
            raise CertificateManagerException("The Manager only accepts parsed readers.")

    @classmethod
    def add_keycontainer(cls, container_bytes, password=None):
        '''
        Adds the key container to the database
        :return: AddKeyContainerResult
        '''
        try:
            reader = ContainerDetector.factory(container_bytes, password)
            reader.parse()
            if isinstance(reader, (PKCS1Reader, PKCS8Reader)):
                return cls._add_privatekey(reader)
            if isinstance(reader, X509Reader):
                return cls._add_x509(reader)
            if isinstance(reader, PKCS12Reader):
                return cls._add_pkcs12(reader)
        except Exception as e:
            return AddKeyContainerResult(False, exceptions=[e])

    @classmethod
    def _add_privatekey(cls, reader):
        '''
        Adds a private key to the database
        :return AddKeyContainerResult
        '''
        cls._check_if_parsed(reader)
        cert_exists = not cls._certificate_by_hash(reader.public_key_hash()) == None
        if not cert_exists:
            e = CertificateManagerException(
                "It exists no certificate for this private key. Add a certificate first.")
            return AddKeyContainerResult(False, exceptions=[e])
        already_exists = not cls._privatekey_by_hash(reader.public_key_hash()) == None
        if already_exists:
            e = CertificateManagerException(
                "Private key already exists.")
            return AddKeyContainerResult(False, exceptions=[e])
        privatekey = strongMan.apps.certificates.models.certificates.PrivateKey.by_reader(reader)
        privatekey.connect_to_certificates()
        return AddKeyContainerResult(True, privatekey=privatekey)

    @classmethod
    def _add_x509(cls, reader):
        '''
        Adds a X509 Certificate to the database
        :return AddKeyContainerResult
        '''
        cls._check_if_parsed(reader)
        already_exists = not cls._certificate_by_hashserial(reader.public_key_hash(), reader.serial_number()) == None
        if already_exists:
            e = CertificateManagerException("Certificate " + reader.cname() + " already exists.")
            return AddKeyContainerResult(False, exceptions=[e])
        cert = strongMan.apps.certificates.models.certificates.CertificateFactory.user_certificate_by_x509reader(reader)
        cert.set_privatekey_if_exists()
        cert.save()
        result = AddKeyContainerResult(True, certificate=cert, further_certificates=[])
        return result

    @classmethod
    def _add_pkcs12(cls, reader):
        '''
        Adds a pkcs12 reader to the database
        :return: AddKeyContainerResult
        '''
        cls._check_if_parsed(reader)

        x509reader = reader.public_key()
        result = cls._add_x509(x509reader)

        private_reader = reader.private_key()
        result += cls._add_privatekey(private_reader)

        further_x509reader = reader.further_publics()
        for x509read in further_x509reader:
            further = UserCertificateManager._add_x509(x509read)
            further.move_certificate_to_further()
            result += further

        result.success = not result.certificates_are_empty()

        return result

    @classmethod
    def _certificate_by_hashserial(cls, publickey_hash, serial_number):
        certs = strongMan.apps.certificates.models.certificates.UserCertificate.objects.filter(
            public_key_hash=publickey_hash, serial_number=serial_number)
        if len(certs) > 0:
            return certs[0]
        else:
            return None

    @classmethod
    def _certificate_by_hash(cls, publickey_hash):
        certs = strongMan.apps.certificates.models.certificates.UserCertificate.objects.filter(
            public_key_hash=publickey_hash)
        if len(certs) > 0:
            return certs[0]
        else:
            return None

    @classmethod
    def _privatekey_by_hash(cls, publickey_hash):
        keys = strongMan.apps.certificates.models.certificates.PrivateKey.objects.filter(public_key_hash=publickey_hash)
        if len(keys) > 0:
            return keys[0]
        else:
            return None


class CertificateManagerException(Exception):
    pass


class AddEapSecretResult:
    def __init__(self, success, username = None, password = None, exceptions=[]):
        self.success = success
        self.username = username
        self.password = password
        self.exceptions = exceptions

    def __add__(self, other):
        if self.certificate is not None and other.certificate is not None:
            raise CertificateManagerException("Can't add two certificates")
        if self.privatekey is not None and other.privatekey is not None:
            raise CertificateManagerException("Can't add two privatekeys")

        result = AddEapSecretResultResult(True)
        result.success = not (not self.success or not other.success)
        if other.certificate is not None:
            result.certificate = other.certificate
        if self.certificate is not None:
            result.certificate = self.certificate

        if other.privatekey is not None:
            result.privatekey = other.privatekey
        if self.privatekey is not None:
            result.privatekey = self.privatekey

        result.further_certificates = self.further_certificates + other.further_certificates
        result.exceptions = self.exceptions + other.exceptions

        return result

    def __iadd__(self, other):
        return self + other

    def move_certificate_to_further(self):
        '''
        Moves the single certificate to the further_certificates list
        :return: None
        '''
        if self.certificate is not None:
            self.further_certificates.append(self.certificate)
            self.certificate = None

    def certificates_are_empty(self):
        return self.certificate is None and self.privatekey is None and len(self.further_certificates) == 0
