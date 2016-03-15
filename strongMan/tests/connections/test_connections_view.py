from django.test import TestCase, Client
from django.contrib.auth.models import User
from strongMan.apps.connections.models import Connection


class ConnectionModelTest(TestCase):

    def setUp(self):
        self.client = Client()
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser', password='12345')

    def test_select_post(self):
        response = self.client.post('/connection/create/0', {'typ': '2'})
        self.assertEquals('/connection/create/2', response.url)

    def test_Ike2CertificateForm_post(self):
        url = '/connection/create/1'
        self.client.post(url, {'gateway': "gateway", 'profile': 'profile'})
        self.assertEquals(1, Connection.objects.count())

    def test_Ike2EapForm_post(self):
        url = '/connection/create/2'
        response = self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password"})
        self.assertEquals(1, Connection.objects.count())
