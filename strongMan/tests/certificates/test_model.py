from django.test import TestCase, RequestFactory
from strongMan.apps.certificates.models import Certificate, PrivateKey, Domain, SubjectInfo
from strongMan.apps.certificates.request_handler import AddHandler
import os


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



class TestCert:
    def __init__(self, path):
        self.path = path
        self.current_dir = os.path.dirname(os.path.realpath(__file__))

    def open(self):
        absolute_path = self.current_dir + "/certs/" + self.path
        return open(absolute_path, 'rb')

    def add_to_db(self):
        with CreateRequest("/certificates/add", self) as request:
            handler = AddHandler.by_request(request)
            (req, page, context) = handler.handle()
            assert "certificates/added.html" == page


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
    X509_googlecom = TestCert("google.com_der.crt")


def count(model):
    return model.objects.all().__len__()


class ModelTest(TestCase):
    def test_add_to_db(self):
        Paths.PKCS12_rsa.add_to_db()
        self.assertEquals(count(Certificate), 2)
        self.assertEqual(count(Domain), 2)
        self.assertEquals(count(SubjectInfo), 4)
        self.assertEquals(count(PrivateKey), 1)

    def test_delete_privatekey(self):
        Paths.PKCS12_rsa.add_to_db()
        self.assertEquals(count(PrivateKey), 1)
        PrivateKey.objects.all().delete()
        self.assertEquals(count(PrivateKey), 0)
        self.assertEquals(count(Certificate), 2)
        self.assertEqual(count(Domain), 2)
        self.assertEquals(count(SubjectInfo), 4)

        for certificate in Certificate.objects.all():
            self.assertIsNone(certificate.private_key, "Private keys should be none")

    def test_delete_domain(self):
        Paths.PKCS12_rsa.add_to_db()
        self.assertEquals(count(Certificate), 2)
        self.assertEqual(count(Domain), 2)
        self.assertEquals(count(SubjectInfo), 4)
        self.assertEquals(count(PrivateKey), 1)
        Domain.objects.all().delete()
        self.assertEqual(count(Domain), 0)
        self.assertEquals(count(Certificate), 2, "Certificate should not be deleted")
        self.assertEquals(count(SubjectInfo), 4)
        self.assertEquals(count(PrivateKey), 1)

    def test_delete_subjectinfo(self):
        Paths.PKCS12_rsa.add_to_db()
        self.assertEquals(count(Certificate), 2)
        self.assertEqual(count(Domain), 2)
        self.assertEquals(count(SubjectInfo), 4)
        self.assertEquals(count(PrivateKey), 1)
        SubjectInfo.objects.all().delete()
        self.assertEquals(count(SubjectInfo), 0)
        self.assertEquals(count(Certificate), 2, "Certificate should not be deleted")
        self.assertEqual(count(Domain), 2)
        self.assertEquals(count(PrivateKey), 1)

    def test_delete_certificate_without_privatekey(self):
        Paths.PKCS12_rsa.add_to_db()
        ca_list = Certificate.objects.filter(is_CA=True)
        self.assertEquals(ca_list.__len__(), 1)
        ca_list[0].delete()
        self.assertEquals(count(Certificate), 1)
        self.assertEquals(count(SubjectInfo), 2)
        self.assertEqual(count(Domain), 1)
        self.assertEquals(count(PrivateKey), 1)

    def test_delete_certificate_with_privatekey(self):
        Paths.PKCS12_rsa.add_to_db()
        ca_list = Certificate.objects.filter(is_CA=False)
        self.assertEquals(ca_list.__len__(), 1)
        ca_list[0].delete()
        self.assertEquals(count(Certificate), 1)
        self.assertEquals(count(SubjectInfo), 2)
        self.assertEqual(count(Domain), 1)
        self.assertEquals(count(PrivateKey), 0)



