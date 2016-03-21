from django.test import TestCase, RequestFactory, Client
from strongMan.apps.certificates.forms import AddForm, AddHandler
from strongMan.apps.certificates.models import Certificate, PrivateKey
import os

def create_request(page, context):
        factory = RequestFactory()
        request = factory.post(page, context)
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request

class TestCert:
    def __init__(self, path):
        self.path = path
        self.current_dir = os.path.dirname(os.path.realpath(__file__))

    def open(self):
        absolute_path = self.current_dir + "/certs/" + self.path
        return open(absolute_path, 'rb')


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


class AddHandlerTest(TestCase):
    def certificates_count(self):
        return Certificate.objects.all().__len__()

    def privatekeys_count(self):
        return PrivateKey.objects.all().__len__()

    def test_x509(self):
        f = Paths.X509_rsa_ca.open()
        request = create_request("/certificates/add", {'password': "", "cert": f})
        handler = AddHandler.by_request(request)
        (req, page, context) = handler.handle()
        f.close()
        self.assertEqual("certificates/added.html", page)
        self.assertTrue(context['public'].is_CA)
        self.assertEqual(1, self.certificates_count())

    def test_x509_with_pw(self):
        f = Paths.X509_rsa_ca.open()
        request = create_request("/certificates/add", {'password': "fasdfa", "cert": f})
        handler = AddHandler.by_request(request)
        (req, page, context) = handler.handle()
        f.close()
        self.assertEqual("certificates/add.html", page)
        self.assertEqual(0, self.certificates_count())

    def test_pkcs1_without_certificate(self):
        f = Paths.PKCS1_ec.open()
        request = create_request("/certificates/add", {'password': "", "cert": f})
        handler = AddHandler.by_request(request)
        (req, page, context) = handler.handle()
        f.close()
        self.assertEqual("certificates/add.html", page)
        self.assertEqual(0, self.certificates_count())

    def test_pkcs1_with_certificate(self):
        self.test_x509() # Add x509
        f = Paths.PKCS1_rsa_ca.open()
        request = create_request("/certificates/add", {'password': "", "cert": f})
        handler = AddHandler.by_request(request)
        (req, page, context) = handler.handle()
        f.close()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])

    def test_pkcs8_with_certificate(self):
        self.test_x509() # Add x509
        f = Paths.PKCS8_rsa_ca.open()
        request = create_request("/certificates/add", {'password': "", "cert": f})
        handler = AddHandler.by_request(request)
        (req, page, context) = handler.handle()
        f.close()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])

    def test_pkcs8_with_certificate_encrypted(self):
        self.test_x509() # Add x509
        f = Paths.PKCS8_rsa_ca_encrypted.open()
        request = create_request("/certificates/add", {'password': "strongman", "cert": f})
        handler = AddHandler.by_request(request)
        (req, page, context) = handler.handle()
        f.close()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])

    def test_pkcs12(self):
        f = Paths.PKCS12_rsa.open()
        request = create_request("/certificates/add", {'password': "", "cert": f})
        handler = AddHandler.by_request(request)
        (req, page, context) = handler.handle()
        f.close()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertEqual(2, self.certificates_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])
        self.assertIsNotNone(context["further_publics"])

    def test_pkcs12_encrypted(self):
        f = Paths.PKCS12_rsa_encrypted.open()
        request = create_request("/certificates/add", {'password': "strongman", "cert": f})
        handler = AddHandler.by_request(request)
        (req, page, context) = handler.handle()
        f.close()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertEqual(2, self.certificates_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])
        self.assertIsNotNone(context["further_publics"])

    def test_pkcs12_encrypted_no_pw(self):
        f = Paths.PKCS12_rsa_encrypted.open()
        request = create_request("/certificates/add", {'password': "", "cert": f})
        handler = AddHandler.by_request(request)
        (req, page, context) = handler.handle()
        f.close()
        self.assertEqual("certificates/add.html", page)
        self.assertEqual(0, self.privatekeys_count())
        self.assertEqual(0, self.certificates_count())

    def test_pkcs12_ca_already_imported(self):
        self.test_x509() # Add x509 CA
        self.assertEqual(1, self.certificates_count(), "CA imported.")
        f = Paths.PKCS12_rsa.open()
        request = create_request("/certificates/add", {'password': "", "cert": f})
        handler = AddHandler.by_request(request)
        (req, page, context) = handler.handle()
        f.close()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertEqual(2, self.certificates_count(), "CA should not be duplicated.")
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])
        self.assertIsNotNone(context["further_publics"])






















