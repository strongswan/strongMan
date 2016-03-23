from django.test import TestCase, Client
from django.contrib.auth.models import User
from strongMan.apps.connections.models import Connection, Typ
from strongMan.apps.certificates.models import Domain, Certificate


class ConnectionViewTest(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.client = Client()
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser', password='12345')
        certificate = Certificate(serial_number="007", is_CA=True, valid_not_after="2011-09-01T13:20:30+03:00",
                                  valid_not_before="2011-09-01T13:20:30+03:00")
        certificate.save()
        Domain(value="test.pem", certificate=certificate).save()

    def test_select_post(self):
        response = self.client.post('/connection/create/0', {'typ': '2'})
        self.assertEquals(response.status_code, 302)

    def test_Ike2CertificateCreate_post(self):
        url = '/connection/create/1'
        domain = Domain.objects.first()

        self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'certificate': domain.id})

        self.assertEquals(1, Connection.objects.count())

    def test_Ike2CertificateCreate_update(self):
        url_create = '/connection/create/1'
        domain = Domain.objects.first()

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