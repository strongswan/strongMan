import os

from django.test import TestCase

import strongMan.apps.certificates.models.certificates
import strongMan.apps.certificates.models as models
from strongMan.apps.certificates import container_reader
from strongMan.apps.certificates.container_reader import ContainerTypes, ContainerDetector, AbstractContainerReader, \
    X509Reader, PKCS12Reader, PrivateReader

from .certificates import TestCertificates


class ContainerDetectorTest(TestCase):
    def test_read_file_x509(self):
        bytes = TestCertificates.X509_rsa_ca.read()
        self.assertIsNotNone(bytes)

    def get_type(self, testcert, password=None):
        '''
        Return the detected type of the testcert
        :param testcert: CertificateLoader
        :return: a string ["Private" | "PKCS12" | "X509" | None]
        '''
        bytes = testcert.read()
        if password is None:
            format = ContainerDetector.detect_type(bytes)
        else:
            format = ContainerDetector.detect_type(bytes, password=password)
        return format.value

    def test_X509_type(self):
        self.assertEqual(self.get_type(TestCertificates.X509_rsa_ca), "X509")
        self.assertEqual(self.get_type(TestCertificates.X509_rsa_ca_der), "X509")
        self.assertEqual(self.get_type(TestCertificates.X509_ec), "X509")
        self.assertEqual(self.get_type(TestCertificates.X509_rsa), "X509")

    def test_privatekey_type(self):
        self.assertEqual(self.get_type(TestCertificates.PKCS1_rsa_ca), "Private")
        self.assertEqual(self.get_type(TestCertificates.PKCS8_rsa_ca), "Private")
        self.assertEqual(self.get_type(TestCertificates.PKCS1_ec), "Private")

    def test_pkcs1_encrypted_type(self):
        self.assertEqual(self.get_type(TestCertificates.PKCS1_rsa_ca_encrypted, b"strongman"), "Private")

    def test_pkcs1_encrypted_type_without_pw(self):
        self.assertEqual(self.get_type(TestCertificates.PKCS1_rsa_ca_encrypted, None), None)

    def test_pkcs12_type(self):
        self.assertEqual(self.get_type(TestCertificates.PKCS12_rsa), "PKCS12")

    def test_pkcs12_type_encrypted(self):
        self.assertEqual(self.get_type(TestCertificates.PKCS12_rsa_encrypted, b"strongman"), "PKCS12")

    def test_pkcs12_type_encrypted_without_pw(self):
        self.assertEqual(self.get_type(TestCertificates.PKCS12_rsa_encrypted, None), None)


class AbstractContainerTest(TestCase):
    def create_test_container(self, testcert):
        bytes = testcert.read()
        container = AbstractContainerReader.by_bytes(bytes)
        return container

    def test_constructor(self):
        container = self.create_test_container(TestCertificates.X509_rsa_ca)
        self.assertIsNotNone(container.bytes)
        self.assertEqual(container.type, ContainerTypes.X509)


class PCKS1Test(TestCase):
    def test_parse(self):
        bytes = TestCertificates.PKCS1_rsa_ca.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.asn1)

    def test_algorithm_rsa(self):
        bytes = TestCertificates.PKCS1_rsa_ca.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        self.assertEqual(container.algorithm(), "rsa")

    def test_algorithm_ec(self):
        bytes = TestCertificates.PKCS1_ec.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        self.assertEqual(container.algorithm(), "ec")

    def test_dump_rsa(self):
        bytes = TestCertificates.PKCS1_rsa_ca.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.der_dump())

    def test_dump_rsa(self):
        bytes = TestCertificates.PKCS1_ec.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.der_dump())

    def test_identifier_rsa(self):
        bytes = TestCertificates.PKCS1_rsa_ca.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        should = "FA:CC:60:F4:20:6B:25:C7:A4:AD:1D:FE:37:C4:76:09:73:07:BE:35:E9:50:2B:28:1A:10:6A:30:2C:09:D4:A9"
        ident = str(container.public_key_hash())
        self.assertEqual(ident, should)

    def test_identifier_ec(self):
        bytes = TestCertificates.PKCS1_ec.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        should = "7D:83:F3:D5:9F:B1:CC:36:2B:50:E7:FD:7A:45:A1:60:63:48:FB:58:B7:AA:31:7A:A1:C4:B5:D4:C1:59:82:CE"
        ident = container.public_key_hash()
        self.assertEqual(ident, should)

    def test_decryption(self):
        bytes = TestCertificates.PKCS1_rsa_ca_encrypted.read()
        container = PrivateReader.by_bytes(bytes, password=b"strongman")
        container.parse()
        self.assertEqual(container.algorithm(), "rsa")

    def test_to_private_key(self):
        bytes = TestCertificates.PKCS1_ec.read()
        priv = PrivateReader.by_bytes(bytes)
        priv.parse()
        privatekey = strongMan.apps.certificates.models.certificates.PrivateKey.by_reader(priv)
        self.assertIsNotNone(privatekey)
        self.assertIsNotNone(privatekey.algorithm)
        self.assertIsNotNone(privatekey.der_container)

    def test_dsa(self):
        bytes = TestCertificates.PKCS1_dsa.read()
        x509 = PrivateReader.by_bytes(bytes)
        with self.assertRaises(Exception):
            x509.parse()


class PCKS8Test(TestCase):
    def test_parse(self):
        bytes = TestCertificates.PKCS8_rsa_ca.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.asn1)

    def test_algorithm_rsa(self):
        bytes = TestCertificates.PKCS8_rsa_ca.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        self.assertEqual(container.algorithm(), "rsa")

    def test_algorithm_ec(self):
        bytes = TestCertificates.PKCS8_ec.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        self.assertEqual(container.algorithm(), "ec")

    def test_dump_rsa(self):
        bytes = TestCertificates.PKCS8_rsa_ca.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.der_dump())

    def test_dump_rsa(self):
        bytes = TestCertificates.PKCS8_ec.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.der_dump())

    def test_identifier_rsa(self):
        bytes = TestCertificates.PKCS8_rsa_ca.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        should = "FA:CC:60:F4:20:6B:25:C7:A4:AD:1D:FE:37:C4:76:09:73:07:BE:35:E9:50:2B:28:1A:10:6A:30:2C:09:D4:A9"
        ident = str(container.public_key_hash())
        self.assertEqual(ident, should)

    def test_identifier_ec(self):
        bytes = TestCertificates.PKCS8_ec.read()
        container = PrivateReader.by_bytes(bytes)
        container.parse()
        should = "7D:83:F3:D5:9F:B1:CC:36:2B:50:E7:FD:7A:45:A1:60:63:48:FB:58:B7:AA:31:7A:A1:C4:B5:D4:C1:59:82:CE"
        ident = container.public_key_hash()
        self.assertEqual(ident, should)

    def test_decryption(self):
        bytes = TestCertificates.PKCS8_rsa_ca_encrypted.read()
        container = PrivateReader.by_bytes(bytes, password=b"strongman")
        container.parse()
        self.assertEqual(container.algorithm(), "rsa")

    def test_to_private_key(self):
        bytes = TestCertificates.PKCS8_ec.read()
        x509 = PrivateReader.by_bytes(bytes)
        x509.parse()
        public = strongMan.apps.certificates.models.certificates.PrivateKey.by_reader(x509)
        self.assertIsNotNone(public)
        self.assertIsNotNone(public.algorithm)
        self.assertIsNotNone(public.der_container)


class PCKS12ContainerTest(TestCase):
    def test_parse(self):
        bytes = TestCertificates.PKCS12_rsa.read()
        container = PKCS12Reader.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.privatekey)
        self.assertIsNotNone(container.cert)
        self.assertIsNotNone(container.certs)

    def test_identifier_rsa(self):
        bytes = TestCertificates.PKCS12_rsa.read()
        container = PKCS12Reader.by_bytes(bytes)
        container.parse()
        should = "0A:69:D0:D8:23:68:16:8A:81:3A:9E:4A:EF:55:F4:D4:11:7F:95:C3:9C:42:55:A6:F6:A4:8F:01:23:9B:FC:C2"
        ident = str(container.public_key_hash())
        self.assertEqual(ident, should)

    def test_decryption(self):
        bytes = TestCertificates.PKCS12_rsa_encrypted.read()
        container = PKCS12Reader.by_bytes(bytes, password=b"strongman")
        container.parse()
        self.assertEqual(container.algorithm(), "rsa")

    def test_x509(self):
        bytes = TestCertificates.PKCS12_rsa.read()
        containe = PKCS12Reader.by_bytes(bytes)
        containe.parse()
        cert = strongMan.apps.certificates.models.certificates.CertificateFactory.user_certificate_by_x509reader(
            containe.public_key())
        self.assertIsInstance(cert, strongMan.apps.certificates.models.certificates.Certificate)

    def test_private_key(self):
        bytes = TestCertificates.PKCS12_rsa.read()
        containe = PKCS12Reader.by_bytes(bytes)
        containe.parse()
        key = containe.private_key()
        self.assertIsInstance(key, container_reader.PrivateReader)

    def test_other_x509(self):
        bytes = TestCertificates.PKCS12_rsa.read()
        container = PKCS12Reader.by_bytes(bytes)
        container.parse()
        certs = container.further_publics()
        for c in certs:
            self.assertIsInstance(c, X509Reader)

    def test_identifier_equal(self):
        bytes = TestCertificates.PKCS12_rsa.read()
        container = PKCS12Reader.by_bytes(bytes)
        container.parse()
        private = strongMan.apps.certificates.models.certificates.PrivateKey.by_reader(container.private_key())
        public = strongMan.apps.certificates.models.certificates.CertificateFactory.user_certificate_by_x509reader(
            container.public_key())
        self.assertEqual(private.public_key_hash, public.public_key_hash)


class X509ContainerTest(TestCase):
    def test_parse(self):
        bytes = TestCertificates.X509_rsa_ca.read()
        container = X509Reader.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.asn1)

    def test_algorithm_rsa(self):
        bytes = TestCertificates.X509_rsa_ca.read()
        container = X509Reader.by_bytes(bytes)
        container.parse()
        self.assertEqual(container.algorithm(), "rsa")

    def test_algorithm_ec(self):
        bytes = TestCertificates.X509_ec.read()
        container = X509Reader.by_bytes(bytes)
        container.parse()
        self.assertEqual(container.algorithm(), "ec")

    def test_dump_rsa(self):
        bytes = TestCertificates.X509_rsa_ca.read()
        container = X509Reader.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.der_dump())

    def test_dump_rsa(self):
        bytes = TestCertificates.X509_ec.read()
        container = X509Reader.by_bytes(bytes)
        container.parse()
        self.assertIsNotNone(container.der_dump())

    def test_identifier_rsa(self):
        bytes = TestCertificates.X509_rsa_ca.read()
        container = X509Reader.by_bytes(bytes)
        container.parse()
        should = "FA:CC:60:F4:20:6B:25:C7:A4:AD:1D:FE:37:C4:76:09:73:07:BE:35:E9:50:2B:28:1A:10:6A:30:2C:09:D4:A9"
        ident = str(container.public_key_hash())
        self.assertEqual(ident, should)

    def test_identifier_ec(self):
        bytes = TestCertificates.X509_ec.read()
        container = X509Reader.by_bytes(bytes)
        container.parse()
        should = "7D:83:F3:D5:9F:B1:CC:36:2B:50:E7:FD:7A:45:A1:60:63:48:FB:58:B7:AA:31:7A:A1:C4:B5:D4:C1:59:82:CE"
        ident = container.public_key_hash()
        self.assertEqual(ident, should)

    def test_is_private_key(self):
        bytes = TestCertificates.X509_rsa_ca.read()
        x509 = X509Reader.by_bytes(bytes)
        x509.parse()

        bytes = TestCertificates.PKCS1_rsa_ca.read()
        key = PrivateReader.by_bytes(bytes)
        key.parse()
        self.assertTrue(x509.is_cert_of(key))

    def test_is_private_key_not(self):
        bytes = TestCertificates.X509_ec.read()
        x509 = X509Reader.by_bytes(bytes)
        x509.parse()

        bytes = TestCertificates.PKCS1_rsa_ca.read()
        key = PrivateReader.by_bytes(bytes)
        key.parse()
        self.assertFalse(x509.is_cert_of(key))

    def test_to_public_key(self):
        bytes = TestCertificates.X509_rsa_ca.read()
        x509 = X509Reader.by_bytes(bytes)
        x509.parse()
        public = strongMan.apps.certificates.models.certificates.CertificateFactory.user_certificate_by_x509reader(x509)
        self.assertIsNotNone(public)
        self.assertIsNotNone(public.subject)
        self.assertIsNotNone(public.issuer)

    def test_dsa(self):
        bytes = TestCertificates.X509_dsa.read()
        x509 = X509Reader.by_bytes(bytes)
        with self.assertRaises(Exception):
            x509.parse()
