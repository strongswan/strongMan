import os
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase, RequestFactory, Client

from strongMan.apps.certificates.models.certificates import PrivateKey, Certificate
from strongMan.apps.certificates.views import AddHandler

from .certificates import TestCertificates


class CreateRequest(object):
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

    def test_x509_with_pw(self):
        with CreateRequest("/certificates/add", TestCertificates.X509_rsa_ca, password="asdfasdf") as request:
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


class DetailsViewTest(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.client.login(username='testuser', password='12345')
        self.factory = RequestFactory()

    def add_keycontainer(self, test_cert, password=""):
        file = test_cert.open()
        context = {"password": password, "cert": file}
        response = self.client.post(reverse('certificates:add'), context)
        file.close()
        self.assertContains(response, "added")

        def count(self, model):
            return model.objects.all().__len__()

    def count(self, model):
        return model.objects.all().__len__()

    def test_add_keycontainer(self):
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.assertEqual(self.count(Certificate), 1)

    def test_main_overview_empty(self):
        self.assertEqual(self.count(Certificate), 0)
        response = self.client.post(reverse('certificates:overview'), {})
        self.assertContains(response, 'id="no_certs_to_show"', 1)

    def test_main_overview_certs(self):
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.add_keycontainer(TestCertificates.X509_googlecom)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:overview'), {})
        self.assertContains(response, 'CN=hsr.ch', 1)
        self.assertContains(response, 'CN=google.com', 1)

    def test_overview_ca_cert(self):
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.add_keycontainer(TestCertificates.X509_googlecom)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:overview_ca'), {})
        self.assertContains(response, 'CN=hsr.ch', 1)
        self.assertNotContains(response, 'CN=google.com')

    def test_overview_certs(self):
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.add_keycontainer(TestCertificates.X509_googlecom)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:overview_certs'), {})
        self.assertNotContains(response, 'CN=hsr.ch')
        self.assertContains(response, 'CN=google.com', 1)

    def test_main_overview_search(self):
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.add_keycontainer(TestCertificates.X509_googlecom)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:overview'), {"search_text": "youtube", "page": 1})
        self.assertNotContains(response, 'CN=hsr.ch')
        self.assertContains(response, 'CN=google.com', 1)

    def test_show_cert_details(self):
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.add_keycontainer(TestCertificates.X509_googlecom)
        self.add_keycontainer(TestCertificates.PKCS1_rsa_ca)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}), {})
        self.assertContains(response, 'hsr.ch')
        self.assertContains(response, '<td>Private</td>')

    def test_details_remove_privatekey(self):
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.add_keycontainer(TestCertificates.X509_googlecom)
        self.add_keycontainer(TestCertificates.PKCS1_rsa_ca)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}),
                                    {"remove_privatekey": "remove_privatekey"})
        self.assertContains(response, 'hsr.ch')
        self.assertNotContains(response, '<td>Private</td>')

    def test_details_remove_cert(self):
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.add_keycontainer(TestCertificates.X509_googlecom)
        self.add_keycontainer(TestCertificates.PKCS1_rsa_ca)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}),
                                    {"remove_cert": "remove_cert"})
        self.assertEqual(self.count(Certificate), 1)

    def test_add_same_publickey_different_serialnumber(self):
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.add_keycontainer(TestCertificates.X509_rsa_ca_samepk_differentsn)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:overview'), {})
        self.assertContains(response, 'CN=hsr.ch', 2)
        self.assertContains(response, 'OU=Informatik', 1)
        self.assertContains(response, 'OU=IT', 1)

    def test_detail_same_publickey_different_serialnumber(self):
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.add_keycontainer(TestCertificates.X509_rsa_ca_samepk_differentsn)
        self.add_keycontainer(TestCertificates.PKCS1_rsa_ca)
        self.assertEqual(self.count(Certificate), 2)
        self.assertEqual(self.count(PrivateKey), 1)

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}), {})
        self.assertContains(response, 'hsr.ch')
        self.assertContains(response, 'IT')
        self.assertContains(response, '<td>Private</td>')

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "2"}), {})
        self.assertContains(response, 'hsr.ch')
        self.assertContains(response, 'Informatik')
        self.assertContains(response, '<td>Private</td>')

    def test_delete_privatekey_same_publickey_different_serialnumber(self):
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.add_keycontainer(TestCertificates.X509_rsa_ca_samepk_differentsn)
        self.add_keycontainer(TestCertificates.PKCS1_rsa_ca)
        self.assertEqual(self.count(Certificate), 2)
        self.assertEqual(self.count(PrivateKey), 1)

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}),
                                    {"remove_privatekey": "remove_privatekey"})
        self.assertEqual(self.count(PrivateKey), 1)

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}), {})
        self.assertNotContains(response, '<td>Private</td>')

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "2"}), {})
        self.assertContains(response, '<td>Private</td>')

    def test_delete_cert_same_publickey_different_serialnumber(self):
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.add_keycontainer(TestCertificates.X509_rsa_ca_samepk_differentsn)
        self.add_keycontainer(TestCertificates.PKCS1_rsa_ca)

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}),
                                    {"remove_cert": "remove_cert"})
        self.assertEqual(self.count(Certificate), 1)
        self.assertEqual(self.count(PrivateKey), 1)

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}), {})
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "2"}), {})
        self.assertContains(response, 'hsr.ch')
        self.assertContains(response, '<td>Private</td>')

    def test_cert_search(self):
        self.add_keycontainer(TestCertificates.X509_rsa)
        self.add_keycontainer(TestCertificates.X509_rsa_ca)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:overview'), {"search_text": "warrior"})

        self.assertContains(response, '=roadwarrior.hsr.ch')
        self.assertNotContains(response, '=hsr.ch')

    def test_change_nickname(self):
        self.add_keycontainer(TestCertificates.X509_rsa)
        self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}),
                         {"update_nickname": "", "nickname": "hulk"})

        cert = Certificate.objects.first().subclass()
        self.assertEqual(cert.nickname, "hulk")
