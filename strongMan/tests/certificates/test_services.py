from django.test import TestCase
import pickle
import os

import strongMan.apps.certificates.models.certificates
from strongMan.apps.certificates.services import UserCertificateManager, ViciCertificateManager, \
    CertificateManagerException
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
    X509_rsa_ca_samepublickey_differentserialnumber_san = TestCert("cacert_gleicher_public_anderer_serial.der")
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
        bytes = Paths.X509_googlecom.read()
        self.manager.add_keycontainer(bytes)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 1)

    def test_add_x509_san_mail(self):
        bytes = Paths.X509_rsa_ca_samepublickey_differentserialnumber_san.read()
        self.manager.add_keycontainer(bytes)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 1)

    def test_add_x509_twice(self):
        bytes = Paths.X509_rsa_ca.read()
        self.manager.add_keycontainer(bytes)
        result = self.manager.add_keycontainer(bytes)
        self.assertEqual(len(result.exceptions), 1)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 1)

    def test_add_x509_twice_different_serialnumber(self):
        self.manager.add_keycontainer(Paths.X509_rsa_ca.read())
        self.manager.add_keycontainer(Paths.X509_rsa_ca_samepublickey_differentserialnumber.read())
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 2)

    def test_add_pkcs1_withx509_twice_different_serialnumber(self):
        self.manager.add_keycontainer(Paths.X509_rsa_ca.read())
        self.manager.add_keycontainer(Paths.X509_rsa_ca_samepublickey_differentserialnumber.read())
        self.manager.add_keycontainer(Paths.PKCS1_rsa_ca.read())
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.PrivateKey), 1)
        for cert in strongMan.apps.certificates.models.certificates.UserCertificate.objects.all():
            self.assertIsNotNone(cert.private_key)

    def test_add_privatekey_without_cert(self):
        bytes = Paths.PKCS1_rsa_ca.read()
        result = self.manager.add_keycontainer(bytes)
        self.assertEqual(len(result.exceptions), 1)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.PrivateKey), 0)

    def test_add_privatekey_with_cert(self):
        self.manager.add_keycontainer(Paths.X509_rsa_ca.read())
        self.manager.add_keycontainer(Paths.PKCS1_rsa_ca.read())
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.PrivateKey), 1)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 1)

    def test_add_privatekey_twice(self):
        self.manager.add_keycontainer(Paths.X509_rsa_ca.read())
        self.manager.add_keycontainer(Paths.PKCS1_rsa_ca.read())
        result = self.manager.add_keycontainer(Paths.PKCS1_rsa_ca.read())
        self.assertEqual(len(result.exceptions), 1)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.PrivateKey), 1)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 1)


class SerializedDict:
    def __init__(self, path):
        self.path = path
        self.folder = os.path.dirname(os.path.realpath(__file__)) + "/vici_certdict/"

    def deserialize(self):
        with open(self.folder + self.path, 'rb') as f:
            return pickle.load(f)


class ViciDict:
    cert = SerializedDict('cert.dict')
    cert_with_private = SerializedDict('certwithprivate.dict')


class TestViciCertificateManager(TestCase):
    def setUp(self):
        self.manager = ViciCertificateManager

    def test_add_vici_user_already_exists(self):
        UserCertificateManager._add_x509(Paths.X509_rsa_ca.read_x509())
        self.manager._add_x509(ViciDict.cert_with_private.deserialize())
        with self.assertRaises(CertificateManagerException):
            self.manager._add_x509(ViciDict.cert.deserialize())
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.ViciCertificate), 1)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 1)
