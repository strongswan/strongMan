from django.test import TestCase
import os
from strongMan.apps.certificates.services import UserCertificateManager, CertificateManagerException
from strongMan.apps.certificates.container_reader import X509Reader, PKCS1Reader
from strongMan.apps.certificates import models

def count(model):
    return model.objects.all().__len__()


class TestCert:
    def __init__(self, path):
        self.path = path
        self.current_dir = os.path.dirname(os.path.realpath(__file__))

    def read(self):
        absolute_path = self.current_dir + "/certs/" + self.path
        with open(absolute_path, 'rb') as f:
            return f.read()

    def read_x509(self, password=None):
        bytes = self.read()
        reader = X509Reader.by_bytes(bytes, password)
        reader.parse()
        return reader

    def read_pkcs1(self, password=None):
        bytes = self.read()
        reader = PKCS1Reader.by_bytes(bytes, password)
        reader.parse()
        return reader


class Paths:
    X509_rsa_ca = TestCert("ca.crt")
    X509_rsa_ca_samepublickey_differentserialnumber = TestCert("hsrca_doppelt_gleicher_publickey.crt")
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
    X509_googlecom = TestCert("google.com_der.crt")

class TestUserCertificateManager(TestCase):
    def setUp(self):
        self.manager = UserCertificateManager

    def test_add_x509(self):
        reader = Paths.X509_rsa_ca.read_x509()
        self.manager.add_x509(reader)
        self.assertEqual(count(models.UserCertificate), 1)

    def test_add_x509_twice(self):
        reader = Paths.X509_rsa_ca.read_x509()
        self.manager.add_x509(reader)
        with self.assertRaises(CertificateManagerException):
            self.manager.add_x509(reader)
        self.assertEqual(count(models.UserCertificate), 1)

    def test_add_x509_without_parsed(self):
        reader = X509Reader.by_bytes(Paths.X509_rsa_ca.read())
        with self.assertRaises(CertificateManagerException):
            self.manager.add_x509(reader)
        self.assertEqual(count(models.UserCertificate), 0)

    def test_add_x509_wrong_reader(self):
        reader = Paths.PKCS1_rsa_ca.read_pkcs1()
        with self.assertRaises(CertificateManagerException):
            self.manager.add_x509(reader)

    def test_add_x509_twice_different_serialnumber(self):
        self.manager.add_x509(Paths.X509_rsa_ca.read_x509())
        self.manager.add_x509(Paths.X509_rsa_ca_samepublickey_differentserialnumber.read_x509())
        self.assertEqual(count(models.UserCertificate), 2)

    def test_add_pkcs1_withx509_twice_different_serialnumber(self):
        self.manager.add_x509(Paths.X509_rsa_ca.read_x509())
        self.manager.add_x509(Paths.X509_rsa_ca_samepublickey_differentserialnumber.read_x509())
        self.manager.add_pkcs1_or_8(Paths.PKCS1_rsa_ca.read_pkcs1())
        self.assertEqual(count(models.PrivateKey), 1)
        for cert in models.UserCertificate.objects.all():
            self.assertIsNotNone(cert.private_key)

    def test_add_privatekey_without_cert(self):
        reader = Paths.PKCS1_rsa_ca.read_pkcs1()
        with self.assertRaises(CertificateManagerException):
            self.manager.add_pkcs1_or_8(reader)
        self.assertEqual(count(models.PrivateKey), 0)

    def test_add_privatekey_wrong_reader(self):
        reader = Paths.X509_rsa_ca.read_x509()
        with self.assertRaises(CertificateManagerException):
            self.manager.add_pkcs1_or_8(reader)

    def test_add_privatekey_with_cert(self):
        self.manager.add_x509(Paths.X509_rsa_ca.read_x509())
        reader = Paths.PKCS1_rsa_ca.read_pkcs1()
        self.manager.add_pkcs1_or_8(reader)
        self.assertEqual(count(models.PrivateKey), 1)
        self.assertEqual(count(models.UserCertificate), 1)

    def test_add_privatekey_twice(self):
        self.manager.add_x509(Paths.X509_rsa_ca.read_x509())
        self.manager.add_pkcs1_or_8(Paths.PKCS1_rsa_ca.read_pkcs1())
        with self.assertRaises(CertificateManagerException):
            self.manager.add_pkcs1_or_8(Paths.PKCS1_rsa_ca.read_pkcs1())
        self.assertEqual(count(models.PrivateKey), 1)
        self.assertEqual(count(models.UserCertificate), 1)



























