import os

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase, Client

from strongMan.apps.certificates.models.certificates import Certificate
from strongMan.apps.certificates.services import UserCertificateManager
from strongMan.apps.connections.models.connections import Connection, IKEv2Certificate

from strongMan.tests.tests.certificates.certificates import TestCertificates


class ConnectionViewTest(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.client.login(username='testuser', password='12345')
        manager = UserCertificateManager()
        manager.add_keycontainer(TestCertificates.PKCS12_rsa.read())

        certificate = Certificate.objects.first()
        self.certificate = certificate.subclass()
        self.identity = self.certificate.identities.first()

    def test_select_post(self):
        response = self.client.post('/connections/add/',
                                    {'current_form': 'ChooseTypeForm', 'typ': 'Ike2EapForm',
                                     'form_name': 'Ike2EapForm'})
        self.assertEqual(response.status_code, 200)

    def test_Ike2CertificateCreate_post(self):
        url = '/connections/add/'
        res = self.client.post(url, {'current_form': 'Ike2CertificateForm', 'gateway': "gateway", 'profile': 'profile',
                                     'certificate': self.certificate.pk, 'identity': self.identity.pk,
                                     'certificate_ca': self.certificate.pk, 'identity_ca': "fsdasdfadfs",
                                     'form_name': 'Ike2CertificateForm'})
        self.assertEqual(1, Connection.objects.count())

    def test_Ike2CertificateCreate_update(self):
        url_create = '/connections/add/'
        self.client.post(url_create, {'current_form': 'Ike2CertificateForm', 'gateway': "gateway", 'profile': 'profile',
                                      'certificate': self.certificate.pk, 'identity': self.identity.pk,
                                      'certificate_ca': self.certificate.pk, 'identity_ca': "adsfasdfasdf",
                                      'form_name': 'Ike2CertificateForm'})

        connection_created = Connection.objects.first().subclass()
        self.assertEqual(connection_created.profile, 'profile')

        url_update = '/connections/' + str(connection_created.id) + '/'
        self.client.post(url_update, {'current_form': 'Ike2CertificateForm', 'gateway': "gateway", 'profile': 'hans',
                                      'certificate': self.certificate.pk, 'identity': self.identity.pk,
                                      'certificate_ca': self.certificate.pk, 'identity_ca': "ffffff",
                                      'form_name': 'Ike2CertificateForm', 'wizard_step': 'configure'})

        connection = Connection.objects.first().subclass()
        self.assertEqual(connection.profile, 'hans')

    def test_Ike2EapCreate_post(self):
        url = '/connections/add/'
        self.client.post(url, {'current_form': 'Ike2EapForm', 'gateway': "gateway", 'profile': 'profile',
                               'username': "username", 'password': "password",
                               'certificate_ca': self.certificate.pk, 'identity_ca': "ffffff"})
        self.assertEqual(1, Connection.objects.count())

    def test_Ike2EapUpdate_post(self):
        url_create = '/connections/add/'
        response = self.client.post(url_create,
                                    {'current_form': 'Ike2EapForm', 'gateway': "gateway", 'profile': 'profile',
                                     'username': "username", 'password': "password",
                                     'certificate_ca': self.certificate.pk, 'identity_ca': "asdfasdfasdfa"})

        connection_created = Connection.objects.first().subclass()
        self.assertEqual(connection_created.profile, 'profile')

        url_update = '/connections/' + str(connection_created.id) + '/'
        self.client.post(url_update, {'current_form': 'Ike2EapForm', 'gateway': "gateway", 'profile': 'hans',
                                      'username': "username", 'password': "password",
                                      'certificate_ca': self.certificate.pk, 'identity_ca': "fasdfasdf"})

        connection = Connection.objects.first().subclass()
        self.assertEqual(connection.profile, 'hans')

    def test_Ike2EapCertificateCreate_post(self):
        url = '/connections/add/'

        self.client.post(url, {'current_form': 'Ike2CertificateForm', 'gateway': "gateway", 'profile': 'profile',
                               'username': "username", 'password': "password",
                               'certificate': self.certificate.pk, 'identity': self.identity.pk,
                               'certificate_ca': self.certificate.pk, 'identity_ca': "adsfasdf",
                               'form_name': 'Ike2EapCertificateForm'})

        self.assertEqual(1, Connection.objects.count())

    # TODO Ike2EapCertificate create

    def test_Ike2EapCertificateCreate_update(self):
        url_create = '/connections/add/'

        self.client.post(url_create, {'current_form': 'Ike2CertificateForm', 'gateway': "gateway", 'profile': 'profile',
                                      'username': "username", 'password': "password",
                                      'certificate': self.certificate.pk, 'identity': self.identity.pk,
                                      'certificate_ca': self.certificate.pk, 'identity_ca': "adsfasdfasdf",
                                      'form_name': 'Ike2EapCertificateForm'})

        connection_created = Connection.objects.first().subclass()
        self.assertEqual(connection_created.profile, 'profile')

        url_update = '/connections/' + str(connection_created.id) + '/'
        self.client.post(url_update, {'current_form': 'Ike2CertificateForm', 'gateway': "gateway", 'profile': 'hans',
                                      'username': "username", 'password': "password",
                                      'certificate': self.certificate.pk, 'identity': self.identity.pk,
                                      'certificate_ca': self.certificate.pk, 'identity_ca': "fffff",
                                      'form_name': 'Ike2EapCertificateForm'})

        connection = Connection.objects.first().subclass()
        self.assertEqual(connection.profile, 'hans')

    def test_delete_post(self):
        connection = IKEv2Certificate(profile='rw', auth='pubkey', version=1)
        connection.save()
        url = '/connections/delete/' + str(connection.id) + '/'
        self.assertEqual(1, Connection.objects.count())
        self.client.post(url)
        self.assertEqual(0, Connection.objects.count())

    def test_certificate_picker_rendering(self):
        url = reverse("connections:certificatepicker")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_ca_picker_rendering(self):
        url = reverse("connections:capicker")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
