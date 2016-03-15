from oscrypto import keys as k
from asn1crypto import keys
from enum import Enum
from .models import PublicKey, PrivateKey, SubjectInfo

class ContainerTypes(Enum):
    PKCS1="PKCS1"
    PKCS8="PKCS8"
    PKCS12="PKCS12"
    X509="X509"
    Undefined=None


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
        if cls._is_pkcs12(container_bytes, password=password): return ContainerTypes.PKCS12
        elif cls._is_pkcs8(container_bytes, password=password): return ContainerTypes.PKCS8
        elif cls._is_pkcs1(container_bytes, password=password): return ContainerTypes.PKCS1
        elif cls._is_x509(container_bytes, password=password): return ContainerTypes.X509
        else: return ContainerTypes.Undefined


class AbstractContainer:
    def __init__(self):
        self.bytes = None
        self.type = None
        self.password = None

    @classmethod
    def by_bytes(cls, bytes, password=None):
        container = cls()
        container.bytes = bytes
        container.type = ContainerDetector.detect_type(bytes, password=password)
        container.password = password
        return container

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

    def identifier(self):
        '''
        Return a public key like identifier. The identifier can be compare with other to find the private key / certificate pair
        :return: Identifier
        '''
        raise NotImplementedError()

    def algorithm(self):
        '''
        :return: "rsa" or "ec"
        '''
        raise NotImplementedError()



class PKCS1Container(AbstractContainer):
    def parse(self):
        assert self.type == ContainerTypes.PKCS1
        if self.password == None:
            self.asn1 = k.parse_private(self.bytes)
        else:
            self.asn1 = k.parse_private(self.bytes, password=self.password)
        self.asn1.native

    def der_dump(self):
        return self.asn1.dump()

    def identifier(self):
        if self.algorithm() == "rsa":
            return self._pubkey_rsa()
        elif self.algorithm() == "ec":
             return self._pubkey_ec()

    def algorithm(self):
        return self.asn1.algorithm


    def _pubkey_rsa(self):
        private = keys.RSAPrivateKey.load(self.asn1.native["private_key"])
        return private.native["modulus"]

    def _pubkey_ec(self):
        private = keys.ECPrivateKey.load(self.asn1.native["private_key"])
        return private.native["public_key"]

    def to_private_key(self):
        '''
        Transforms this container to a savable PrivateKey
        :return: models.PrivateKey
        '''
        private = PrivateKey()
        private.algorithm = self.algorithm()
        private.der_container = self.der_dump()
        private.type = self.type
        return private


class PKCS8Container(AbstractContainer):
    def parse(self):
        assert self.type == ContainerTypes.PKCS8
        if self.password == None:
            self.asn1 = k.parse_private(self.bytes)
        else:
            self.asn1 = k.parse_private(self.bytes, password=self.password)
        self.asn1.native

    def der_dump(self):
        return self.asn1.dump()

    def identifier(self):
        if self.algorithm() == "rsa":
            return self.asn1.native["private_key"]["modulus"]
        elif self.algorithm() == "ec":
            return self.asn1.native["private_key"]["public_key"]

    def algorithm(self):
        return self.asn1.algorithm

    def to_private_key(self):
        '''
        Transforms this container to a savable PrivateKey
        :return: models.PrivateKey
        '''
        private = PrivateKey()
        private.algorithm = self.algorithm()
        private.der_container = self.der_dump()
        private.type = self.type
        return private


class PKCS12Container(AbstractContainer):
    def parse(self):
        assert self.type == ContainerTypes.PKCS12
        if self.password == None:
            (self.privatekey, self.cert, self.certs) = k.parse_pkcs12(self.bytes)
        else:
            (self.privatekey, self.cert, self.certs) = k.parse_pkcs12(self.bytes, password=self.password)

    def algorithm(self):
        return self.privatekey.algorithm

    def identifier(self):
        if self.algorithm() == "rsa":
            return self.privatekey.native["private_key"]["modulus"]
        elif self.algorithm() == "ec":
            return self.privatekey.native["private_key"]["public_key"]

    def x509(self):
        '''
        :return: the main X509 cert in this container
        :rtype X509Container
        '''
        bytes = self.cert.dump()
        container = X509Container.by_bytes(bytes)
        container.parse()
        return container

    def pkcs8(self):
        '''
        :return: The private key in this container
        :rtype PKCS8Container
        '''
        bytes = self.privatekey.dump()
        container = PKCS8Container.by_bytes(bytes)
        container.parse()
        return container

    def other_x509(self):
        '''
        :return: A list of X509 certs
        :rtype [X509Container]
        '''
        others = []
        for cer in self.certs:
            bytes = cer.dump()
            x509 = X509Container.by_bytes(bytes)
            x509.parse()
            others.append(x509)
        return others


class X509Container(AbstractContainer):
    def parse(self):
        assert self.type == ContainerTypes.X509
        self.asn1 = k.parse_certificate(self.bytes)
        self.asn1.native

    def der_dump(self):
        return self.asn1.dump()

    def algorithm(self):
        return self.asn1.native["tbs_certificate"]["subject_public_key_info"]["algorithm"]["algorithm"]

    def identifier(self):
        if self.algorithm() == "rsa":
            return self.asn1.native["tbs_certificate"]["subject_public_key_info"]["public_key"]["modulus"]
        elif self.algorithm() == "ec":
            return self.asn1.native["tbs_certificate"]["subject_public_key_info"]["public_key"]

    def is_cert_of(self, container):
        '''
        Compares the public keys of the container and this
        :param container: a private key container
        :type container: AbstractContainer
        :return: Boolean
        '''
        ident = container.identifier()
        myident = self.identifier()
        return ident == myident

    def to_public_key(self):
        '''
        Transforms this X509 certificate to a saveble PublicKey
        :return: models.PublicKey
        '''
        public = PublicKey()
        public.der_container = self.der_dump()
        public.type = self.type.value
        public.algorithm = self.algorithm()
        public.hash_algorithm = self.asn1.hash_algo
        public.serial_number = self.asn1.serial_number
        public.is_CA = self.asn1.ca
        public.valid_not_after = self.asn1.native["tbs_certificate"]["validity"]["not_after"]
        public.valid_not_before = self.asn1.native["tbs_certificate"]["validity"]["not_before"]
        public.issuer = SubjectInfo()
        public.issuer.location = self.asn1.issuer.native["locality_name"]
        public.issuer.cname = self.asn1.issuer.native["common_name"]
        public.issuer.country = self.asn1.issuer.native["country_name"]
        public.issuer.email = self.asn1.issuer.native["email_address"]
        public.issuer.organization = self.asn1.issuer.native["organization_name"]
        public.issuer.unit = self.asn1.issuer.native["organizational_unit_name"]
        public.issuer.province = self.asn1.issuer.native["state_or_province_name"]
        public.subject = SubjectInfo()
        public.subject.location = self.asn1.subject.native["locality_name"]
        public.subject.cname = self.asn1.subject.native["common_name"]
        public.subject.country = self.asn1.subject.native["country_name"]
        public.subject.email = self.asn1.subject.native["email_address"]
        public.subject.organization = self.asn1.subject.native["organization_name"]
        public.subject.unit = self.asn1.subject.native["organizational_unit_name"]
        public.subject.province = self.asn1.subject.native["state_or_province_name"]
        return  public



