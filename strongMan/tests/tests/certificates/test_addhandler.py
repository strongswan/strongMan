import os

from django.test import TestCase, RequestFactory

from strongMan.apps.certificates.models.certificates import PrivateKey, Certificate
from strongMan.apps.certificates.views import AddHandler

from .certificates import TestCertificates


class CreateRequest:
    '''
    This class is a with object. __enter__ opens a file and __exit__ closes the file.
    with CreateRequest(page, testcert) as request:
        Do stuff #!#!#!
    '''

    def __init__(self, page, testcert, password=""):
        self.page = page
        self.testcert = testcert
        self.password = password
        self.file = None

    def _create_request(self, page, context):
        factory = RequestFactory()
        request = factory.post(page, context)
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request

    def __enter__(self):
        self.file = self.testcert.open()
        context = {"password": self.password, "cert": self.file}
        request = self._create_request(self.password, context)
        return request

    def __exit__(self, type, value, traceback):
        self.file.close()


class AddHandlerTest(TestCase):
    def certificates_count(self):
        return Certificate.objects.all().__len__()

    def privatekeys_count(self):
        return PrivateKey.objects.all().__len__()

    def test_x509(self):
        with CreateRequest("/certificates/add", TestCertificates.X509_rsa_ca) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
            self.assertEqual("certificates/added.html", page)
            self.assertTrue(context['public'].is_CA)
            self.assertEqual(1, self.certificates_count())
            self.assertEqual(0, self.privatekeys_count())

    def add_rw_certificate(self):
        with CreateRequest("/certificates/add", TestCertificates.X509_rsa) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()

    def test_x509_valid_domains(self):
        self.add_rw_certificate()  # Add a sample domain

        with CreateRequest("/certificates/add", TestCertificates.X509_googlecom) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()

        self.assertEqual("certificates/added.html", page)
        self.assertTrue(not context['public'].is_CA)
        self.assertEqual(2, self.certificates_count())
        self.assertEqual(0, self.privatekeys_count())
        domains_count = context['public'].identities.all().__len__()
        self.assertEqual(505, domains_count)

    def test_x509_with_pw(self):
        with CreateRequest("/certificates/add", TestCertificates.X509_rsa_ca, password="asdfasdf") as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/add.html", page)
        self.assertEqual(0, self.certificates_count())
        self.assertEqual(0, self.privatekeys_count())

    def test_pkcs1_without_certificate(self):
        with CreateRequest("/certificates/add", TestCertificates.PKCS1_ec) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/add.html", page)
        self.assertEqual(0, self.certificates_count())
        self.assertEqual(0, self.privatekeys_count())

    def test_pkcs1_with_certificate(self):
        self.test_x509()  # Add x509
        with CreateRequest("/certificates/add", TestCertificates.PKCS1_rsa_ca) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])

    def test_pkcs8_with_certificate(self):
        self.test_x509()  # Add x509
        with CreateRequest("/certificates/add", TestCertificates.PKCS8_rsa_ca) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])

    def test_pkcs8_with_certificate_encrypted(self):
        self.test_x509()  # Add x509
        with CreateRequest("/certificates/add", TestCertificates.PKCS8_rsa_ca_encrypted, password="strongman") as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])

    def test_pkcs12(self):
        with CreateRequest("/certificates/add", TestCertificates.PKCS12_rsa) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertEqual(2, self.certificates_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])
        self.assertIsNotNone(context["further_publics"])

    def test_pkcs12_encrypted(self):
        with CreateRequest("/certificates/add", TestCertificates.PKCS12_rsa_encrypted, password="strongman") as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertEqual(2, self.certificates_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])
        self.assertIsNotNone(context["further_publics"])

    def test_pkcs12_encrypted_no_pw(self):
        with CreateRequest("/certificates/add", TestCertificates.PKCS12_rsa_encrypted, password="") as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/add.html", page)
        self.assertEqual(0, self.privatekeys_count())
        self.assertEqual(0, self.certificates_count())

    def test_pkcs12_ca_already_imported(self):
        self.test_x509()  # Add x509 CA
        self.assertEqual(1, self.certificates_count(), "CA imported.")
        with CreateRequest("/certificates/add", TestCertificates.PKCS12_rsa) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertEqual(2, self.certificates_count(), "CA should not be duplicated.")
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])
        self.assertIsNotNone(context["further_publics"])
