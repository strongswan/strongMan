import os

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory, Client

from strongMan.apps.certificates.models import Certificate
from strongMan.apps.certificates.models.certificates import PrivateKey, Certificate
from strongMan.apps.certificates.request_handler.AddHandler import AddHandler


class TestCert:
    def __init__(self, path):
        self.path = path
        self.current_dir = os.path.dirname(os.path.realpath(__file__))

    def open(self):
        absolute_path = self.current_dir + "/certs/" + self.path
        return open(absolute_path, 'rb')


class Paths:
    X509_rsa_ca = TestCert("ca.crt")
    X509_rsa_ca2 = TestCert("hsrca_doppelt_gleicher_publickey.crt")
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
        with CreateRequest("/certificates/add", Paths.X509_rsa_ca) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
            self.assertEqual("certificates/added.html", page)
            self.assertTrue(context['public'].is_CA)
            self.assertEqual(1, self.certificates_count())
            self.assertEqual(0, self.privatekeys_count())

    def add_rw_certificate(self):
        with CreateRequest("/certificates/add", Paths.X509_rsa) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()

    def test_x509_valid_domains(self):
        self.add_rw_certificate()  # Add a sample domain

        with CreateRequest("/certificates/add", Paths.X509_googlecom) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()

        self.assertEqual("certificates/added.html", page)
        self.assertTrue(not context['public'].is_CA)
        self.assertEqual(2, self.certificates_count())
        self.assertEqual(0, self.privatekeys_count())
        domains_count = context['public'].identities.all().__len__()
        self.assertEqual(505, domains_count)

    def test_x509_with_pw(self):
        with CreateRequest("/certificates/add", Paths.X509_rsa_ca, password="asdfasdf") as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/add.html", page)
        self.assertEqual(0, self.certificates_count())
        self.assertEqual(0, self.privatekeys_count())

    def test_pkcs1_without_certificate(self):
        with CreateRequest("/certificates/add", Paths.PKCS1_ec) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/add.html", page)
        self.assertEqual(0, self.certificates_count())
        self.assertEqual(0, self.privatekeys_count())

    def test_pkcs1_with_certificate(self):
        self.test_x509()  # Add x509
        with CreateRequest("/certificates/add", Paths.PKCS1_rsa_ca) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])

    def test_pkcs8_with_certificate(self):
        self.test_x509()  # Add x509
        with CreateRequest("/certificates/add", Paths.PKCS8_rsa_ca) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])

    def test_pkcs8_with_certificate_encrypted(self):
        self.test_x509()  # Add x509
        with CreateRequest("/certificates/add", Paths.PKCS8_rsa_ca_encrypted, password="strongman") as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])

    def test_pkcs12(self):
        with CreateRequest("/certificates/add", Paths.PKCS12_rsa) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertEqual(2, self.certificates_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])
        self.assertIsNotNone(context["further_publics"])

    def test_pkcs12_encrypted(self):
        with CreateRequest("/certificates/add", Paths.PKCS12_rsa_encrypted, password="strongman") as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/added.html", page)
        self.assertEqual(1, self.privatekeys_count())
        self.assertEqual(2, self.certificates_count())
        self.assertIsNotNone(context["public"])
        self.assertIsNotNone(context["private"])
        self.assertIsNotNone(context["further_publics"])

    def test_pkcs12_encrypted_no_pw(self):
        with CreateRequest("/certificates/add", Paths.PKCS12_rsa_encrypted, password="") as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
        self.assertEqual("certificates/add.html", page)
        self.assertEqual(0, self.privatekeys_count())
        self.assertEqual(0, self.certificates_count())

    def test_pkcs12_ca_already_imported(self):
        self.test_x509()  # Add x509 CA
        self.assertEqual(1, self.certificates_count(), "CA imported.")
        with CreateRequest("/certificates/add", Paths.PKCS12_rsa) as request:
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
        self.add_keycontainer(Paths.X509_rsa_ca)
        self.assertEqual(self.count(Certificate), 1)

    def test_main_overview_empty(self):
        self.assertEqual(self.count(Certificate), 0)
        response = self.client.post(reverse('certificates:overview'), {})
        self.assertContains(response, 'id="no_certs_to_show"', 1)

    def test_main_overview_certs(self):
        self.add_keycontainer(Paths.X509_rsa_ca)
        self.add_keycontainer(Paths.X509_googlecom)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:overview'), {})
        self.assertContains(response, 'CN=hsr.ch', 1)
        self.assertContains(response, 'CN=google.com', 1)

    def test_overview_ca_cert(self):
        self.add_keycontainer(Paths.X509_rsa_ca)
        self.add_keycontainer(Paths.X509_googlecom)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:overview_ca'), {})
        self.assertContains(response, 'CN=hsr.ch', 1)
        self.assertNotContains(response, 'CN=google.com')

    def test_overview_certs(self):
        self.add_keycontainer(Paths.X509_rsa_ca)
        self.add_keycontainer(Paths.X509_googlecom)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:overview_certs'), {})
        self.assertNotContains(response, 'CN=hsr.ch')
        self.assertContains(response, 'CN=google.com', 1)

    def test_main_overview_search(self):
        self.add_keycontainer(Paths.X509_rsa_ca)
        self.add_keycontainer(Paths.X509_googlecom)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:overview'), {"search_text": "youtube", "page": 1})
        self.assertNotContains(response, 'CN=hsr.ch')
        self.assertContains(response, 'CN=google.com', 1)

    def test_show_cert_details(self):
        self.add_keycontainer(Paths.X509_rsa_ca)
        self.add_keycontainer(Paths.X509_googlecom)
        self.add_keycontainer(Paths.PKCS1_rsa_ca)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}), {})
        # print(response.content.decode("utf-8"))
        self.assertContains(response, 'hsr.ch')
        self.assertContains(response, 'PKCS1')

    def test_details_remove_privatekey(self):
        self.add_keycontainer(Paths.X509_rsa_ca)
        self.add_keycontainer(Paths.X509_googlecom)
        self.add_keycontainer(Paths.PKCS1_rsa_ca)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}),
                                    {"remove_privatekey": "remove_privatekey"})
        self.assertContains(response, 'hsr.ch')
        self.assertNotContains(response, 'PKCS1')

    def test_details_remove_cert(self):
        self.add_keycontainer(Paths.X509_rsa_ca)
        self.add_keycontainer(Paths.X509_googlecom)
        self.add_keycontainer(Paths.PKCS1_rsa_ca)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}),
                                    {"remove_cert": "remove_cert"})
        self.assertEqual(self.count(Certificate), 1)

    def test_add_same_publickey_different_serialnumber(self):
        self.add_keycontainer(Paths.X509_rsa_ca)
        self.add_keycontainer(Paths.X509_rsa_ca2)
        self.assertEqual(self.count(Certificate), 2)
        response = self.client.post(reverse('certificates:overview'), {})
        self.assertContains(response, 'CN=hsr.ch', 2)
        self.assertContains(response, 'OU=Informatik', 1)
        self.assertContains(response, 'OU=IT', 1)

    def test_detail_same_publickey_different_serialnumber(self):
        self.add_keycontainer(Paths.X509_rsa_ca)
        self.add_keycontainer(Paths.X509_rsa_ca2)
        self.add_keycontainer(Paths.PKCS1_rsa_ca)
        self.assertEqual(self.count(Certificate), 2)
        self.assertEqual(self.count(PrivateKey), 1)

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}), {})
        self.assertContains(response, 'hsr.ch')
        self.assertContains(response, 'IT')
        self.assertContains(response, 'PKCS1')

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "2"}), {})
        self.assertContains(response, 'hsr.ch')
        self.assertContains(response, 'Informatik')
        self.assertContains(response, 'PKCS1')

    def test_delete_privatekey_same_publickey_different_serialnumber(self):
        self.add_keycontainer(Paths.X509_rsa_ca)
        self.add_keycontainer(Paths.X509_rsa_ca2)
        self.add_keycontainer(Paths.PKCS1_rsa_ca)
        self.assertEqual(self.count(Certificate), 2)
        self.assertEqual(self.count(PrivateKey), 1)

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}),
                                    {"remove_privatekey": "remove_privatekey"})
        self.assertEqual(self.count(PrivateKey), 1)

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}), {})
        self.assertNotContains(response, 'PKCS1')

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "2"}), {})
        self.assertContains(response, 'PKCS1')

    def test_delete_cert_same_publickey_different_serialnumber(self):
        self.add_keycontainer(Paths.X509_rsa_ca)
        self.add_keycontainer(Paths.X509_rsa_ca2)
        self.add_keycontainer(Paths.PKCS1_rsa_ca)

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}),
                                    {"remove_cert": "remove_cert"})
        self.assertEqual(self.count(Certificate), 1)
        self.assertEqual(self.count(PrivateKey), 1)

        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "1"}), {})
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse('certificates:details', kwargs={'certificate_id': "2"}), {})
        self.assertContains(response, 'PKCS1')
        self.assertContains(response, 'hsr.ch')
