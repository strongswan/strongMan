from django.test import TestCase
import pickle
import os

import strongMan.apps.certificates.models.certificates
from strongMan.apps.certificates.services import UserCertificateManager, ViciCertificateManager, \
    CertificateManagerException
from strongMan.apps.certificates.container_reader import X509Reader
from strongMan.apps.certificates import models

from .certificates import TestCertificates


def count(model):
    return model.objects.all().__len__()


class TestUserCertificateManager(TestCase):
    def setUp(self):
        self.manager = UserCertificateManager

    def test_add_x509(self):
        bytes = TestCertificates.X509_googlecom.read()
        self.manager.add_keycontainer(bytes)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 1)

    def test_add_x509_san_mail(self):
        bytes = TestCertificates.X509_rsa_ca_samepk_differentsn_san.read()
        self.manager.add_keycontainer(bytes)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 1)

    def test_add_x509_twice(self):
        bytes = TestCertificates.X509_rsa_ca.read()
        self.manager.add_keycontainer(bytes)
        result = self.manager.add_keycontainer(bytes)
        self.assertEqual(len(result.exceptions), 1)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 1)

    def test_add_x509_twice_different_serialnumber(self):
        self.manager.add_keycontainer(TestCertificates.X509_rsa_ca.read())
        self.manager.add_keycontainer(TestCertificates.X509_rsa_ca_samepk_differentsn.read())
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 2)

    def test_add_pkcs1_withx509_twice_different_serialnumber(self):
        self.manager.add_keycontainer(TestCertificates.X509_rsa_ca.read())
        self.manager.add_keycontainer(TestCertificates.X509_rsa_ca_samepk_differentsn.read())
        self.manager.add_keycontainer(TestCertificates.PKCS1_rsa_ca.read())
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.PrivateKey), 1)
        for cert in strongMan.apps.certificates.models.certificates.UserCertificate.objects.all():
            self.assertIsNotNone(cert.private_key)

    def test_add_privatekey_without_cert(self):
        bytes = TestCertificates.PKCS1_rsa_ca.read()
        result = self.manager.add_keycontainer(bytes)
        self.assertEqual(len(result.exceptions), 1)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.PrivateKey), 0)

    def test_add_privatekey_with_cert(self):
        self.manager.add_keycontainer(TestCertificates.X509_rsa_ca.read())
        self.manager.add_keycontainer(TestCertificates.PKCS1_rsa_ca.read())
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.PrivateKey), 1)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 1)

    def test_add_privatekey_twice(self):
        self.manager.add_keycontainer(TestCertificates.X509_rsa_ca.read())
        self.manager.add_keycontainer(TestCertificates.PKCS1_rsa_ca.read())
        result = self.manager.add_keycontainer(TestCertificates.PKCS1_rsa_ca.read())
        self.assertEqual(len(result.exceptions), 1)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.PrivateKey), 1)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 1)


class SerializedDict(object):
    def __init__(self, path):
        self.path = path
        self.folder = os.path.dirname(os.path.realpath(__file__)) + "/vici_certdict/"

    def deserialize(self):
        with open(self.folder + self.path, 'rb') as f:
            return pickle.load(f)


class ViciDict(object):
    cert = SerializedDict('cert.dict')
    cert_with_private = SerializedDict('certwithprivate.dict')


class TestViciCertificateManager(TestCase):
    def setUp(self):
        self.manager = ViciCertificateManager

    def test_add_vici_user_already_exists(self):
        UserCertificateManager._add_x509(TestCertificates.X509_rsa_ca.read_x509())
        self.manager._add_x509(ViciDict.cert_with_private.deserialize())
        with self.assertRaises(CertificateManagerException):
            self.manager._add_x509(ViciDict.cert.deserialize())
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.ViciCertificate), 1)
        self.assertEqual(count(strongMan.apps.certificates.models.certificates.UserCertificate), 1)
