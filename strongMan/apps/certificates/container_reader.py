import binascii
import hashlib
import re as regex
from collections import OrderedDict
from enum import Enum

from oscrypto import keys as k


class ContainerTypes(Enum):
    Private = "Private"
    PKCS12 = "PKCS12"
    X509 = "X509"
    Undefined = None


class AbstractContainerReader(object):
    def __init__(self):
        self.bytes = None
        self.type = None
        self.password = None
        self.asn1 = None
        self._is_parsed = False

    @classmethod
    def by_bytes(cls, container_bytes, password=None):
        container = cls()
        container.bytes = container_bytes
        container.type = ContainerDetector.detect_type(container_bytes, password=password)
        container.password = password
        return container

    def is_parsed(self):
        return self._is_parsed

    def parse(self):
        '''
        Parses the bytes with a asn1 parser
        :return: None
        '''
        raise NotImplementedError()

    def der_dump(self):
        '''
        Dumpes the asn1 structure back to a uncrypted bytearray in DER format
        :return: bytearray
        '''
        raise NotImplementedError()

    def public_key_hash(self):
        '''
        Return a public key identifier. The identifier can be compared with others to find the
        private key/certificate pair
        :return: Identifier
        '''
        raise NotImplementedError()

    @classmethod
    def is_type(cls, container_bytes, password=None):
        '''
        Detects if the bytes have this ASN1 structure
        :return: Boolean
        '''
        raise NotImplementedError()

    def _sha256(self, value):
        '''
        Makes a sha256 hash over a string value. Formats the hash to be readable
        :param value: input
        :return: formated hash
        '''
        value = value.encode('utf-8')
        sha = hashlib.sha256()
        sha.update(value)
        hash_bytes = sha.digest()
        return self._format_hash(hash_bytes)

    def _format_hash(self, hash_bytes):
        hash_hex = binascii.hexlify(hash_bytes)
        hash_upper = hash_hex.decode('utf-8').upper()
        formated_hash = ""
        for part in regex.findall('..', hash_upper):
            formated_hash += part + ":"

        return formated_hash[:-1]

    def _raise_if_wrong_algorithm(self):
        algorithm_lower = self.algorithm().lower()
        wrong_algorihm = not (algorithm_lower == "rsa" or algorithm_lower == "ec")
        if wrong_algorihm:
            raise Exception("Detected unsupported algorithm " + str(algorithm_lower))

    def algorithm(self):
        '''
        :return: "rsa" or "ec"
        '''
        raise NotImplementedError()


class PrivateReader(AbstractContainerReader):
    @classmethod
    def is_type(cls, container_bytes, password=None):
        cert = None
        try:
            if password is None:
                cert = k.parse_private(container_bytes)
            else:
                cert = k.parse_private(container_bytes, password=password)

            cert.native
        except Exception:
            return False

        try:
            if cert.native["private_key"]["modulus"] is not None:
                return True
        except Exception:
            pass

        try:
            if cert.native["private_key"]["public_key"] is not None:
                return True
        except Exception:
            pass

        return False

    def parse(self):
        assert self.type == ContainerTypes.Private
        if self.password is None:
            self.asn1 = k.parse_private(self.bytes)
        else:
            self.asn1 = k.parse_private(self.bytes, password=self.password)
        self.asn1.native
        self._raise_if_wrong_algorithm()
        self._is_parsed = True

    def der_dump(self):
        return self.asn1.dump()

    def public_key_hash(self):
        if self.algorithm() == "rsa":
            ident = self.asn1.native["private_key"]["modulus"]
        elif self.algorithm() == "ec":
            ident = self.asn1.native["private_key"]["public_key"]

        return self._sha256(str(ident))

    def algorithm(self):
        return self.asn1.algorithm


class PKCS12Reader(AbstractContainerReader):
    @classmethod
    def is_type(cls, container_bytes, password=None):
        try:
            if password is None:
                k.parse_pkcs12(container_bytes)
            else:
                k.parse_pkcs12(container_bytes, password=password)
            return True
        except Exception:
            return False

    def parse(self):
        assert self.type == ContainerTypes.PKCS12
        if self.password is None:
            (self.privatekey, self.cert, self.certs) = k.parse_pkcs12(self.bytes)
        else:
            (self.privatekey, self.cert, self.certs) = k.parse_pkcs12(self.bytes, password=self.password)
        self._raise_if_wrong_algorithm()
        self._is_parsed = True

    def algorithm(self):
        return self.privatekey.algorithm

    def public_key_hash(self):
        if self.algorithm() == "rsa":
            ident = self.privatekey.native["private_key"]["modulus"]
        elif self.algorithm() == "ec":
            ident = self.privatekey.native["private_key"]["public_key"]
        return self._sha256(str(ident))

    def public_key(self):
        '''
        :return: the main X509 cert in this container
        :rtype X509Container
        '''
        data = self.cert.dump()
        container = X509Reader.by_bytes(data)
        container.parse()
        return container

    def private_key(self):
        '''
        :return: The private key in this container
        :rtype PrivateContainer
        '''
        data = self.privatekey.dump()
        container = PrivateReader.by_bytes(data)
        container.parse()
        return container

    def further_publics(self):
        '''
        :return: A list of X509 certs
        :rtype [X509Container]
        '''
        others = []
        for cer in self.certs:
            data = cer.dump()
            x509 = X509Reader.by_bytes(data)
            x509.parse()
            others.append(x509)
        return others


class X509Reader(AbstractContainerReader):
    @classmethod
    def is_type(cls, container_bytes, password=None):
        try:
            cert = k.parse_certificate(container_bytes)
            cert.native
            return True
        except Exception:
            return False

    def parse(self):
        assert self.type == ContainerTypes.X509
        self.asn1 = k.parse_certificate(self.bytes)
        self.asn1.native
        self._raise_if_wrong_algorithm()
        self._is_parsed = True

    def der_dump(self):
        return self.asn1.dump()

    def algorithm(self):
        return self.asn1.native["tbs_certificate"]["subject_public_key_info"]["algorithm"]["algorithm"]

    def public_key_hash(self):
        if self.algorithm() == "rsa":
            ident = self.asn1.native["tbs_certificate"]["subject_public_key_info"]["public_key"]["modulus"]
        elif self.algorithm() == "ec":
            ident = self.asn1.native["tbs_certificate"]["subject_public_key_info"]["public_key"]
        return self._sha256(str(ident))

    def is_cert_of(self, container):
        '''
        Compares the public keys of the container and this
        :param container: a private key container
        :type container: AbstractContainerReader
        :return: Boolean
        '''
        ident = container.public_key_hash()
        myident = self.public_key_hash()
        return ident == myident

    def serial_number(self):
        return self.asn1.serial_number

    def cname(self):
        return self.asn1.subject.native["common_name"]


class ContainerReaderException(Exception):
    pass


class ContainerDetector(object):
    _readers = OrderedDict([
        (ContainerTypes.X509, X509Reader),
        (ContainerTypes.PKCS12, PKCS12Reader),
        (ContainerTypes.Private, PrivateReader),
    ])

    @classmethod
    def detect_type(cls, container_bytes, password=None):
        '''
        Detects the type of an ASN.1 container
        :param container_bytes: bytes of the container in PEM or DER
        :param password: password of the container if encrypted
        :return: Type of the container
        :rtype ContainerTypes
        '''
        for ct, reader in cls._readers.items():
            if reader.is_type(container_bytes, password=password):
                return ct
        return ContainerTypes.Undefined

    @classmethod
    def factory(cls, container_bytes, password=None):
        '''
        Creates an instance of an ASN.1 container reader
        :param container_bytes: bytes of the container in PEM or DER
        :param password: password of the container if encrypted
        :return: container reader
        :rtype object derived of AbstractContainerReader
        '''
        reader = cls._readers[cls.detect_type(container_bytes, password)]
        if reader:
            return reader.by_bytes(container_bytes, password)
        raise ContainerReaderException("Can't detect a supported ASN.1 type.")
