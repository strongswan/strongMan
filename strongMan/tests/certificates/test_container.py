from django.test import TestCase
from strongMan.apps.certificates.container import ContainerTypes, ContainerDetector, AbstractContainer, X509Container, PKCS12Container, PKCS1Container, PKCS8Container
import os
import strongMan.apps.certificates.models as models


class TestCert:
    def __init__(self, path):
        self.path = path
        self.current_dir = os.path.dirname(os.path.realpath(__file__))

    def read(self):
        absolute_path = self.current_dir + "/certs/" + self.path
        with open(absolute_path, 'rb') as f:
            return f.read()


class Paths:
    X509_rsa_ca = TestCert("ca.crt")
    PKCS1_rsa_ca = TestCert("ca2.key")
    PKCS1_rsa_ca_encrypted = TestCert("ca.key")
    PKCS8_rsa_ca = TestCert("ca2.pkcs8")
    PKCS8_ec = TestCert("ec.pkcs8")
    PKCS8_rsa_ca_encrypted = TestCert("ca_enrypted.pkcs8")
    X509_rsa_ca_der = TestCert("cacert.der")
    X509_ec = TestCert("ec.crt")
    PKCS1_ec = TestCert("ec2.key")
    X509_rsa = TestCert("warrior.crt")
    PKCS12_rsa = TestCert("warrior.pkcs12")
    PKCS12_rsa_encrypted = TestCert("warrior_encrypted.pkcs12")


class ContainerDetectorTest(TestCase):
    def test_read_file_x509(self):
        bytes = Paths.X509_rsa_ca.read()
        self.assertIsNotNone(bytes)

    def check_type(self, testcert, type, password=None):
        '''
        Check if the testcert has the specific type
        :param testcert: TestCert
        :param type: a string ["PKCS1" | "PKCS8" | "PKCS12" | "X509" | None]
        :return: True or False if the type is right
        '''
        bytes = testcert.read()
        if password is None:
            format = ContainerDetector.detect_type(bytes)
        else:
            format = ContainerDetector.detect_type(bytes, password=password)
        return format.value == type

    def test_X509_type(self):
        self.assertTrue(self.check_type(Paths.X509_rsa_ca, "X509"))
        self.assertTrue(self.check_type(Paths.X509_rsa_ca_der, "X509"))
        self.assertTrue(self.check_type(Paths.X509_ec, "X509"))
        self.assertTrue(self.check_type(Paths.X509_rsa, "X509"))

    def test_privatekey_type(self):
        self.assertTrue(self.check_type(Paths.PKCS1_rsa_ca, "PKCS1"))
        self.assertTrue(self.check_type(Paths.PKCS8_rsa_ca, "PKCS8"))
        self.assertTrue(self.check_type(Paths.PKCS1_ec, "PKCS1"))

    def test_pkcs1_encrypted_type(self):
        self.assertTrue(self.check_type(Paths.PKCS1_rsa_ca_encrypted, "PKCS1", b"strongman"))

    def test_pkcs1_encrypted_type_without_pw(self):
        self.check_type(Paths.PKCS1_rsa_ca_encrypted, None)

    def test_pkcs12_type(self):
        self.assertTrue(self.check_type(Paths.PKCS12_rsa, "PKCS12"))

    def test_pkcs12_type_encrypted(self):
        self.assertTrue(self.check_type(Paths.PKCS12_rsa_encrypted, "PKCS12", b"strongman"))

    def test_pkcs12_type_encrypted_without_pw(self):
        self.assertTrue(self.check_type(Paths.PKCS12_rsa_encrypted, None))


class AbstractContainerTest(TestCase):
    def create_test_container(self, testcert):
        bytes = testcert.read()
        container = AbstractContainer.by_bytes(bytes)
        return container

    def test_constructor(self):
        container = self.create_test_container(Paths.X509_rsa_ca)
        self.assertIsNotNone(container.bytes)
        self.assertEqual(container.type, ContainerTypes.X509)


class PCKS1ContainerTest(TestCase):
    def test_parse(self):
        bytes = Paths.PKCS1_rsa_ca.read()
        container = PKCS1Container.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.asn1)

    def test_algorithm_rsa(self):
        bytes = Paths.PKCS1_rsa_ca.read()
        container = PKCS1Container.by_bytes(bytes)
        container.parse()
        self.assertEqual(container.algorithm(), "rsa")

    def test_algorithm_ec(self):
        bytes = Paths.PKCS1_ec.read()
        container = PKCS1Container.by_bytes(bytes)
        container.parse()
        self.assertEqual(container.algorithm(), "ec")

    def test_dump_rsa(self):
        bytes = Paths.PKCS1_rsa_ca.read()
        container = PKCS1Container.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.der_dump())

    def test_dump_rsa(self):
        bytes = Paths.PKCS1_ec.read()
        container = PKCS1Container.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.der_dump())

    def test_identifier_rsa(self):
        bytes = Paths.PKCS1_rsa_ca.read()
        container = PKCS1Container.by_bytes(bytes)
        container.parse()
        should = "facc60f4206b25c7a4ad1dfe37c476097307be35e9502b281a106a302c09d4a9"
        ident = str(container.identifier())
        self.assertEqual(ident, should)

    def test_identifier_ec(self):
        bytes = Paths.PKCS1_ec.read()
        container = PKCS1Container.by_bytes(bytes)
        container.parse()
        should = "7d83f3d59fb1cc362b50e7fd7a45a1606348fb58b7aa317aa1c4b5d4c15982ce"
        ident = container.identifier()
        self.assertEqual(ident, should)

    def test_decryption(self):
        bytes = Paths.PKCS1_rsa_ca_encrypted.read()
        container = PKCS1Container.by_bytes(bytes, password=b"strongman")
        container.parse()
        self.assertEqual(container.algorithm(), "rsa")

    def test_to_private_key(self):
        bytes = Paths.PKCS1_ec.read()
        x509 = PKCS1Container.by_bytes(bytes)
        x509.parse()
        public = x509.to_private_key()
        self.assertIsNotNone(public)
        self.assertIsNotNone(public.algorithm)
        self.assertIsNotNone(public.der_container)


class PCKS8ContainerTest(TestCase):
    def test_parse(self):
        bytes = Paths.PKCS8_rsa_ca.read()
        container = PKCS8Container.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.asn1)

    def test_algorithm_rsa(self):
        bytes = Paths.PKCS8_rsa_ca.read()
        container = PKCS8Container.by_bytes(bytes)
        container.parse()
        self.assertEqual(container.algorithm(), "rsa")

    def test_algorithm_ec(self):
        bytes = Paths.PKCS8_ec.read()
        container = PKCS8Container.by_bytes(bytes)
        container.parse()
        self.assertEqual(container.algorithm(), "ec")

    def test_dump_rsa(self):
        bytes = Paths.PKCS8_rsa_ca.read()
        container = PKCS8Container.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.der_dump())

    def test_dump_rsa(self):
        bytes = Paths.PKCS8_ec.read()
        container = PKCS8Container.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.der_dump())

    def test_identifier_rsa(self):
        bytes = Paths.PKCS8_rsa_ca.read()
        container = PKCS8Container.by_bytes(bytes)
        container.parse()
        should = "facc60f4206b25c7a4ad1dfe37c476097307be35e9502b281a106a302c09d4a9"
        ident = str(container.identifier())
        self.assertEqual(ident, should)

    def test_identifier_ec(self):
        bytes = Paths.PKCS8_ec.read()
        container = PKCS8Container.by_bytes(bytes)
        container.parse()
        should = "7d83f3d59fb1cc362b50e7fd7a45a1606348fb58b7aa317aa1c4b5d4c15982ce"
        ident = container.identifier()
        self.assertEqual(ident, should)

    def test_decryption(self):
        bytes = Paths.PKCS8_rsa_ca_encrypted.read()
        container = PKCS8Container.by_bytes(bytes, password=b"strongman")
        container.parse()
        self.assertEqual(container.algorithm(), "rsa")

    def test_to_private_key(self):
        bytes = Paths.PKCS8_ec.read()
        x509 = PKCS8Container.by_bytes(bytes)
        x509.parse()
        public = x509.to_private_key()
        self.assertIsNotNone(public)
        self.assertIsNotNone(public.algorithm)
        self.assertIsNotNone(public.der_container)


class PCKS12ContainerTest(TestCase):
    def test_parse(self):
        bytes = Paths.PKCS12_rsa.read()
        container = PKCS12Container.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.privatekey)
        self.assertIsNotNone(container.cert)
        self.assertIsNotNone(container.certs)

    def test_identifier_rsa(self):
        bytes = Paths.PKCS12_rsa.read()
        container = PKCS12Container.by_bytes(bytes)
        container.parse()
        should = "0a69d0d82368168a813a9e4aef55f4d4117f95c39c4255a6f6a48f01239bfcc2"
        ident = str(container.identifier())
        self.assertEqual(ident, should)

    def test_decryption(self):
        bytes = Paths.PKCS12_rsa_encrypted.read()
        container = PKCS12Container.by_bytes(bytes, password=b"strongman")
        container.parse()
        self.assertEqual(container.algorithm(), "rsa")

    def test_x509(self):
        bytes = Paths.PKCS12_rsa.read()
        container = PKCS12Container.by_bytes(bytes)
        container.parse()
        cert = container.to_public_key()
        self.assertIsInstance(cert, models.PublicKey)

    def test_private_key(self):
        bytes = Paths.PKCS12_rsa.read()
        container = PKCS12Container.by_bytes(bytes)
        container.parse()
        key = container.to_private_key()
        self.assertIsInstance(key, models.PrivateKey)

    def test_other_x509(self):
        bytes = Paths.PKCS12_rsa.read()
        container = PKCS12Container.by_bytes(bytes)
        container.parse()
        certs = container.further_publics()
        for c in certs:
            self.assertIsInstance(c, models.PublicKey)

    def test_identifier_equal(self):
        bytes = Paths.PKCS12_rsa.read()
        container = PKCS12Container.by_bytes(bytes)
        container.parse()
        private = container.to_private_key()
        public = container.to_public_key()
        self.assertEqual(private.identifier, public.identifier)


class X509ContainerTest(TestCase):
    def test_parse(self):
        bytes = Paths.X509_rsa_ca.read()
        container = X509Container.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.asn1)

    def test_algorithm_rsa(self):
        bytes = Paths.X509_rsa_ca.read()
        container = X509Container.by_bytes(bytes)
        container.parse()
        self.assertEqual(container.algorithm(), "rsa")

    def test_algorithm_ec(self):
        bytes = Paths.X509_ec.read()
        container = X509Container.by_bytes(bytes)
        container.parse()
        self.assertEqual(container.algorithm(), "ec")

    def test_dump_rsa(self):
        bytes = Paths.X509_rsa_ca.read()
        container = X509Container.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.der_dump())

    def test_dump_rsa(self):
        bytes = Paths.X509_ec.read()
        container = X509Container.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.der_dump())

    def test_identifier_rsa(self):
        bytes = Paths.X509_rsa_ca.read()
        container = X509Container.by_bytes(bytes)
        container.parse()
        should = "facc60f4206b25c7a4ad1dfe37c476097307be35e9502b281a106a302c09d4a9"
        ident = str(container.identifier())
        self.assertEqual(ident, should)

    def test_identifier_ec(self):
        bytes = Paths.X509_ec.read()
        container = X509Container.by_bytes(bytes)
        container.parse()
        should = "7d83f3d59fb1cc362b50e7fd7a45a1606348fb58b7aa317aa1c4b5d4c15982ce"
        ident = container.identifier()
        self.assertEqual(ident, should)

    def test_is_private_key(self):
        bytes = Paths.X509_rsa_ca.read()
        x509 = X509Container.by_bytes(bytes)
        x509.parse()

        bytes = Paths.PKCS1_rsa_ca.read()
        key = PKCS1Container.by_bytes(bytes)
        key.parse()
        self.assertTrue(x509.is_cert_of(key))

    def test_is_private_key_not(self):
        bytes = Paths.X509_ec.read()
        x509 = X509Container.by_bytes(bytes)
        x509.parse()

        bytes = Paths.PKCS1_rsa_ca.read()
        key = PKCS1Container.by_bytes(bytes)
        key.parse()
        self.assertFalse(x509.is_cert_of(key))

    def test_to_public_key(self):
        bytes = Paths.X509_rsa_ca.read()
        x509 = X509Container.by_bytes(bytes)
        x509.parse()
        public = x509.to_public_key()
        self.assertIsNotNone(public)
        self.assertIsNotNone(public.subject)
        self.assertIsNotNone(public.issuer)








