import os
import pickle

from django.test import TestCase, RequestFactory

from strongMan.apps.certificates.container_reader import X509Reader
from strongMan.apps.certificates.models.certificates import PrivateKey, DistinguishedName, Certificate, UserCertificate, \
    ViciCertificate, CertificateFactory
from strongMan.apps.certificates.models.identities import AbstractIdentity, TextIdentity, DnIdentity
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


def add_to_db(certificate):
    with CreateRequest("/certificates/add", certificate) as request:
        handler = AddHandler.by_request(request)
        (req, page, context) = handler.handle()
        assert "certificates/added.html" == page


def count(model):
    return model.objects.all().__len__()


class UserCertificateTest(TestCase):
    def test_add_identites(self):
        add_to_db(TestCertificates.X509_googlecom)
        add_to_db(TestCertificates.X509_rsa)
        cert = UserCertificate.objects.first()
        self.assertEqual(len(cert.identities.all()), 505)
        self.assertEqual(count(TextIdentity), 504)
        self.assertEqual(count(DnIdentity), 2)

    def test_abstractIdentity_subclass(self):
        add_to_db(TestCertificates.X509_googlecom)
        cert = UserCertificate.objects.first()
        for ident in cert.identities.all():
            ident = ident.subclass()
            subclasses = AbstractIdentity.all_subclasses()
            self.assertTrue(isinstance(ident, tuple(subclasses)))

    def test_add_to_db(self):
        add_to_db(TestCertificates.PKCS12_rsa)
        self.assertEqual(count(Certificate), 2)
        self.assertEqual(count(AbstractIdentity), 2)
        self.assertEqual(count(DistinguishedName), 4)
        self.assertEqual(count(PrivateKey), 1)

    def test_encrypted_der_container(self):
        add_to_db(TestCertificates.PKCS12_rsa)
        cert = UserCertificate.objects.first()
        reader = X509Reader.by_bytes(cert.der_container)
        reader.parse()
        self.assertEqual(reader.der_dump(), cert.der_container)

    def test_delete_privatekey(self):
        add_to_db(TestCertificates.PKCS12_rsa)
        self.assertEqual(count(PrivateKey), 1)
        PrivateKey.objects.all().delete()
        self.assertEqual(count(PrivateKey), 0)
        self.assertEqual(count(Certificate), 2)
        self.assertEqual(count(AbstractIdentity), 2)
        self.assertEqual(count(DistinguishedName), 4)

        for certificate in UserCertificate.objects.all():
            self.assertIsNone(certificate.private_key, "Private keys should be none")

    def test_delete_domain(self):
        add_to_db(TestCertificates.PKCS12_rsa)
        self.assertEqual(count(Certificate), 2)
        self.assertEqual(count(AbstractIdentity), 2)
        self.assertEqual(count(DistinguishedName), 4)
        self.assertEqual(count(PrivateKey), 1)
        AbstractIdentity.objects.all().delete()
        self.assertEqual(count(AbstractIdentity), 0)
        self.assertEqual(count(Certificate), 2, "Certificate should not be deleted")
        self.assertEqual(count(DistinguishedName), 4)
        self.assertEqual(count(PrivateKey), 1)

    def test_delete_subjectinfo(self):
        add_to_db(TestCertificates.PKCS12_rsa)
        self.assertEqual(count(Certificate), 2)
        self.assertEqual(count(AbstractIdentity), 2)
        self.assertEqual(count(DistinguishedName), 4)
        self.assertEqual(count(PrivateKey), 1)
        DistinguishedName.objects.all().delete()
        self.assertEqual(count(DistinguishedName), 0)
        self.assertEqual(count(Certificate), 2, "Certificate should not be deleted")
        self.assertEqual(count(AbstractIdentity), 2)
        self.assertEqual(count(PrivateKey), 1)

    def test_delete_certificate_without_privatekey(self):
        add_to_db(TestCertificates.PKCS12_rsa)
        ca_list = Certificate.objects.filter(is_CA=True)
        self.assertEqual(ca_list.__len__(), 1)
        ca_list[0].delete()
        self.assertEqual(count(Certificate), 1)
        self.assertEqual(count(DistinguishedName), 2)
        self.assertEqual(count(AbstractIdentity), 1)
        self.assertEqual(count(PrivateKey), 1)

    def test_delete_certificate_with_privatekey(self):
        add_to_db(TestCertificates.PKCS12_rsa)
        ca_list = Certificate.objects.filter(is_CA=False)
        self.assertEqual(ca_list.__len__(), 1)
        ca_list[0].delete()
        self.assertEqual(count(Certificate), 1)
        self.assertEqual(count(DistinguishedName), 2)
        self.assertEqual(count(AbstractIdentity), 1)
        self.assertEqual(count(PrivateKey), 0)

    def test_CertificateFactory(self):
        x509 = X509Reader.by_bytes(TestCertificates.X509_rsa_ca.read())
        x509.parse()
        certificate = CertificateFactory.user_certificate_by_x509reader(x509)

        self.assertIsInstance(certificate, Certificate)
        self.assertIsInstance(certificate.subject, DistinguishedName)
        self.assertIsInstance(certificate.issuer, DistinguishedName)
        self.assertNotEqual(certificate.public_key_hash, "")
        self.assertEqual(count(Certificate), 1)

    def test_privkey_two_certs_delete_cert(self):
        add_to_db(TestCertificates.X509_rsa_ca)
        add_to_db(TestCertificates.X509_rsa_ca_samepk_differentsn)
        add_to_db(TestCertificates.PKCS1_rsa_ca)
        self.assertEqual(count(Certificate), 2)
        self.assertEqual(count(PrivateKey), 1)
        cert = UserCertificate.objects.get(id=1)
        cert.delete()
        self.assertEqual(count(Certificate), 1)
        self.assertEqual(count(PrivateKey), 1)
        other_ert = UserCertificate.objects.get(id=2)
        self.assertIsNotNone(other_ert.private_key)

    def test_privkey_two_certs_delete_both(self):
        add_to_db(TestCertificates.X509_rsa_ca)
        add_to_db(TestCertificates.X509_rsa_ca_samepk_differentsn)
        add_to_db(TestCertificates.PKCS1_rsa_ca)
        self.assertEqual(count(Certificate), 2)
        self.assertEqual(count(PrivateKey), 1)
        UserCertificate.objects.all().delete()
        self.assertEqual(count(Certificate), 0)
        self.assertEqual(count(PrivateKey), 0)

    def test_privkey_two_certs_delete_key_once(self):
        add_to_db(TestCertificates.X509_rsa_ca)
        add_to_db(TestCertificates.X509_rsa_ca_samepk_differentsn)
        add_to_db(TestCertificates.PKCS1_rsa_ca)
        self.assertEqual(count(Certificate), 2)
        self.assertEqual(count(PrivateKey), 1)
        cert = UserCertificate.objects.get(id=1)
        cert.remove_privatekey()
        self.assertIsNone(cert.private_key)
        cert2 = UserCertificate.objects.get(id=2)
        self.assertIsNotNone(cert2.private_key)

    def test_certificate_identities(self):
        add_to_db(TestCertificates.X509_googlecom)
        classes = [Certificate, UserCertificate]
        for clas in classes:
            cert = clas.objects.first()
            count = len(cert.identities)
            self.assertEqual(count, 505)


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


class ViciCertificateTest(TestCase):
    def test_add(self):
        dict = ViciDict.cert.deserialize()
        vicicert = CertificateFactory.vicicertificate_by_dict(dict)
        self.assertEqual(count(ViciCertificate), 1)
        self.assertFalse(vicicert.has_private_key)

    def test_add_with_private(self):
        dict = ViciDict.cert_with_private.deserialize()
        vicicert = CertificateFactory.vicicertificate_by_dict(dict)
        self.assertEqual(count(ViciCertificate), 1)
        self.assertTrue(vicicert.has_private_key)


class AbstractDjangoClassTest(TestCase):
    def test_abstractidentity_to_subclasses(self):
        add_to_db(TestCertificates.X509_googlecom)
        abstract_ident = AbstractIdentity.objects.all()
        real_ident = AbstractIdentity.subclasses(abstract_ident)
        for ident in real_ident:
            self.assertIsInstance(ident, tuple(AbstractIdentity.all_subclasses()))
