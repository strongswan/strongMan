from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from strongMan.apps.connections.models import Connection
from strongMan.apps.certificates.models import Identity, Certificate
from strongMan.apps.connections import views
from django import forms


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
        response = self.client.post('/connection/create/0', {'typ': '2'})
        self.assertEquals(response.status_code, 302)

    def test_Ike2CertificateCreate_post(self):
        url = '/connection/create/1'
        domain = Identity.objects.first()

        self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'certificate': domain.id})

        self.assertEquals(1, Connection.objects.count())

    def test_Ike2CertificateCreate_update(self):
        url_create = '/connection/create/1'
        domain = Identity.objects.first()

        self.client.post(url_create, {'gateway': "gateway", 'profile': 'profile', 'certificate': domain.id})

        connection_created = Connection.objects.first()
        self.assertEquals(connection_created.profile, 'profile')

        url_update = '/connection/update/1/' + str(connection_created.id) + '/'
        self.client.post(url_update, {'gateway': "gateway", 'profile': 'hans', 'certificate': domain.id})

        connection = Connection.objects.first()
        self.assertEquals(connection.profile, 'hans')

    def test_Ike2EapCreate_post(self):
        url = '/connection/create/2'
        self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password"})
        self.assertEquals(1, Connection.objects.count())

    def test_Ike2EapUpdate_post(self):
        url_create = '/connection/create/2'
        self.client.post(url_create, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password"})
        connection_created = Connection.objects.first()
        self.assertEquals(connection_created.profile, 'profile')

        url_update = '/connection/update/2/' + str(connection_created.id) + '/'
        self.client.post(url_update, {'gateway': "gateway", 'profile': 'hans', 'username': "username", 'password': "password"})

        connection = Connection.objects.first()
        self.assertEquals(connection.profile, 'hans')

    def test_Ike2EapCertificateCreate_post(self):
        url = '/connection/create/3'
        domain = Identity.objects.first()

        self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password", 'certificate': domain.id})

        self.assertEquals(1, Connection.objects.count())

    def test_Ike2EapCertificateCreate_update(self):
        url_create = '/connection/create/3'
        domain = Identity.objects.first()

        self.client.post(url_create, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password", 'certificate': domain.id})

        connection_created = Connection.objects.first()
        self.assertEquals(connection_created.profile, 'profile')

        url_update = '/connection/update/3/' + str(connection_created.id) + '/'
        self.client.post(url_update, {'gateway': "gateway", 'profile': 'hans', 'username': "username", 'password': "password", 'certificate': domain.id})

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
        response = self.client.post('/connection/toggle/', {'id':connection.id})
        self.assertEquals(200, response.status_code)


