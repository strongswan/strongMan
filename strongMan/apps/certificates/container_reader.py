import binascii
import hashlib
import re as regex
from enum import Enum

from asn1crypto import keys
from oscrypto import keys as k



class ContainerTypes(Enum):
    PKCS1 = "PKCS1"
    PKCS8 = "PKCS8"
    PKCS12 = "PKCS12"
    X509 = "X509"
    Undefined = None


class ContainerDetector:
    @classmethod
    def _is_x509(cls, container_bytes, password=None):
        try:
            if password == None:
                cert = k.parse_certificate(container_bytes)
            else:
                cert = k.parse_certificate(container_bytes, password=password)

            cert.native
            return True
        except Exception as e:
            return False

    @classmethod
    def _is_pkcs1(cls, container_bytes, password=None):
        if cls._is_pkcs8(bytes, password=password): return False
        try:
            if password == None:
                cert = k.parse_private(container_bytes)
            else:
                cert = k.parse_private(container_bytes, password=password)

            cert.native
            return True
        except Exception as e:
            return False

    @classmethod
    def _is_pkcs8(cls, container_bytes, password=None):
        cert = None
        try:
            if password == None:
                cert = k.parse_private(container_bytes)
            else:
                cert = k.parse_private(container_bytes, password=password)

            cert.native
        except Exception as e:
            return False

        try:
            if cert.native["private_key"]["modulus"] is not None:
                return True
        except:
            pass

        try:
            if cert.native["private_key"]["public_key"] is not None:
                return True
        except:
            pass

        return False

    @classmethod
    def _is_pkcs12(cls, container_bytes, password=None):
        try:
            if password == None:
                k.parse_pkcs12(container_bytes)
            else:
                k.parse_pkcs12(container_bytes, password=password)
            return True
        except Exception as e:
            return False

    @classmethod
    def detect_type(cls, container_bytes, password=None):
        '''
        Detects the type of a ASN1 container
        :param container_bytes: bytes of the container in PEM or DER
        :param password: password of the container if encrypted
        :type password: bytearray like b"mystring"
        :return: Type of the container
        :rtype ContainerTypes
        '''
        if cls._is_pkcs12(container_bytes, password=password):
            return ContainerTypes.PKCS12
        elif cls._is_pkcs8(container_bytes, password=password):
            return ContainerTypes.PKCS8
        elif cls._is_pkcs1(container_bytes, password=password):
            return ContainerTypes.PKCS1
        elif cls._is_x509(container_bytes, password=password):
            return ContainerTypes.X509
        else:
            return ContainerTypes.Undefined


class AbstractContainerReader:
    def __init__(self):
        self.bytes = None
        self.type = None
        self.password = None
        self.asn1 = None

    @classmethod
    def by_bytes(cls, bytes, password=None):
        container = cls()
        container.bytes = bytes
        container.type = ContainerDetector.detect_type(bytes, password=password)
        container.password = password
        return container

    def is_parsed(self):
        return not self.asn1 == None

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
        Return a public key like identifier. The identifier can be compare with other to find the private key / certificate pair
        :return: Identifier
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


class PKCS1Reader(AbstractContainerReader):
    def parse(self):
        assert self.type == ContainerTypes.PKCS1
        if self.password == None:
            self.asn1 = k.parse_private(self.bytes)
        else:
            self.asn1 = k.parse_private(self.bytes, password=self.password)
        self.asn1.native
        self._raise_if_wrong_algorithm()

    def der_dump(self):
        return self.asn1.dump()

    def public_key_hash(self):
        if self.algorithm() == "rsa":
            ident = self._pubkey_rsa()
        elif self.algorithm() == "ec":
            ident = self._pubkey_ec()
        return self._sha256(str(ident))

    def algorithm(self):
        return self.asn1.algorithm

    def _pubkey_rsa(self):
        private = keys.RSAPrivateKey.load(self.asn1.native["private_key"])
        return private.native["modulus"]

    def _pubkey_ec(self):
        private = keys.ECPrivateKey.load(self.asn1.native["private_key"])
        return private.native["public_key"]


class PKCS8Reader(AbstractContainerReader):
    def parse(self):
        assert self.type == ContainerTypes.PKCS8
        if self.password == None:
            self.asn1 = k.parse_private(self.bytes)
        else:
            self.asn1 = k.parse_private(self.bytes, password=self.password)
        self.asn1.native
        self._raise_if_wrong_algorithm()

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
    def parse(self):
        assert self.type == ContainerTypes.PKCS12
        if self.password == None:
            (self.privatekey, self.cert, self.certs) = k.parse_pkcs12(self.bytes)
        else:
            (self.privatekey, self.cert, self.certs) = k.parse_pkcs12(self.bytes, password=self.password)
        self._raise_if_wrong_algorithm()

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
        bytes = self.cert.dump()
        container = X509Reader.by_bytes(bytes)
        container.parse()
        return container

    def private_key(self):
        '''
        :return: The private key in this container
        :rtype PKCS8Container
        '''
        bytes = self.privatekey.dump()
        container = PKCS8Reader.by_bytes(bytes)
        container.parse()
        return container

    def further_publics(self):
        '''
        :return: A list of X509 certs
        :rtype [X509Container]
        '''
        others = []
        for cer in self.certs:
            bytes = cer.dump()
            x509 = X509Reader.by_bytes(bytes)
            x509.parse()
            others.append(x509)
        return others


class X509Reader(AbstractContainerReader):

    def parse(self):
        assert self.type == ContainerTypes.X509
        self.asn1 = k.parse_certificate(self.bytes)
        self.asn1.native
        self._raise_if_wrong_algorithm()

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

    def _try_to_get_value(self, dict, key_path=[], default=None):
        try:
            temp_dict = dict
            for key in key_path:
                temp_dict = temp_dict[key]

            return temp_dict
        except:
            return default

    def serial_number(self):
        return self.asn1.serial_number

    def cname(self):
        return self.asn1.subject.native["common_name"]

