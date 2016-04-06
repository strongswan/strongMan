from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from strongMan.apps.connections.models import Connection
from strongMan.apps.certificates.models import Identity, Certificate
from strongMan.apps.connections import views


class ConnectionViewTest(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.client.login(username='testuser', password='12345')
        certificate = Certificate(serial_number="007", is_CA=True, valid_not_after="2011-09-01T13:20:30+03:00",
                                  valid_not_before="2011-09-01T13:20:30+03:00")
        certificate.save()
        identity = Identity.factory("test.pem")
        identity.certificate=certificate
        identity.save()
        self.factory = RequestFactory()

    def test_select_post(self):
        response = self.client.post('/connections/create/', {'typ': 'Ike2CertificateForm', 'form_name': 'Ike2CertificateForm'})
        self.assertEquals(response.status_code, 200)

    def test_Ike2CertificateCreate_post(self):
        url = '/connections/create/'
        domain = Identity.objects.first()

        self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'certificate': domain.id, 'form_name': 'Ike2CertificateForm'})

        self.assertEquals(1, Connection.objects.count())

    def test_Ike2CertificateCreate_update(self):
        url_create = '/connections/create/'
        domain = Identity.objects.first()

        self.client.post(url_create, {'gateway': "gateway", 'profile': 'profile', 'certificate': domain.id, 'form_name': 'Ike2CertificateForm'})

        connection_created = Connection.objects.first()
        self.assertEquals(connection_created.profile, 'profile')

        url_update = '/connections/' + str(connection_created.id) + '/'
        self.client.post(url_update, {'gateway': "gateway", 'profile': 'hans', 'certificate': domain.id, 'form_name': 'Ike2CertificateForm'})

        connection = Connection.objects.first()
        self.assertEquals(connection.profile, 'hans')

    def test_Ike2EapCreate_post(self):
        url = '/connections/create/'
        self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password", 'form_name': 'Ike2EapForm'})
        self.assertEquals(1, Connection.objects.count())

    def test_Ike2EapUpdate_post(self):
        url_create = '/connections/create/'
        self.client.post(url_create, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password", 'form_name': 'Ike2EapForm'})
        connection_created = Connection.objects.first()
        self.assertEquals(connection_created.profile, 'profile')

        url_update = '/connections/' + str(connection_created.id) + '/'
        self.client.post(url_update, {'gateway': "gateway", 'profile': 'hans', 'username': "username", 'password': "password", 'form_name': 'Ike2EapForm'})

        connection = Connection.objects.first()
        self.assertEquals(connection.profile, 'hans')

    def test_Ike2EapCertificateCreate_post(self):
        url = '/connections/create/'
        domain = Identity.objects.first()

        self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password", 'certificate': domain.id, 'form_name': 'Ike2EapCertificateForm'})

        self.assertEquals(1, Connection.objects.count())

    def test_Ike2EapCertificateCreate_update(self):
        url_create = '/connections/create/'
        domain = Identity.objects.first()

        self.client.post(url_create, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password", 'certificate': domain.id, 'form_name': 'Ike2EapCertificateForm'})

        connection_created = Connection.objects.first()
        self.assertEquals(connection_created.profile, 'profile')

        url_update = '/connections/' + str(connection_created.id) + '/'
        self.client.post(url_update, {'gateway': "gateway", 'profile': 'hans', 'username': "username", 'password': "password", 'certificate': domain.id, 'form_name': 'Ike2EapCertificateForm'})

        connection = Connection.objects.first()
        self.assertEquals(connection.profile, 'hans')

    def test_delete_post(self):
        connection = Connection(profile='rw', auth='pubkey', version=1)
        connection.save()
        self.assertEquals(1, Connection.objects.count())
        request = self.factory.get('/')
        request.user = self.user
        views.delete_connection(request, connection.id)
        self.assertEquals(0, Connection.objects.count())

    def test_toggle_connection_post(self):
        connection = Connection(profile='rw', auth='pubkey', version=1)
        connection.save()
        response = self.client.post('/connections/toggle/', {'id':connection.id})
        self.assertEquals(200, response.status_code)


