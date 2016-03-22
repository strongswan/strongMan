from django.test import TestCase, Client
from django.contrib.auth.models import User
from strongMan.apps.connections.models import Connection, Typ
from strongMan.apps.connections.forms import Ike2CertificateForm
from strongMan.apps.certificates.models import Domain, Certificate


class ConnectionViewTest(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.client = Client()
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser', password='12345')

    def test_select_post(self):
        response = self.client.post('/connection/create/0', {'typ': '2'})
        self.assertEquals(response.status_code, 302)

    def test_Ike2CertificateForm_post(self):
        certificate = Certificate(serial_number="007", is_CA=True, valid_not_after="2011-09-01T13:20:30+03:00", valid_not_before="2011-09-01T13:20:30+03:00")
        certificate.save()
        domain = Domain(value="test.pem", certificate=certificate)
        domain.save()
        url = '/connection/create/1'

        response = self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'certificate': domain.id})

        self.assertEquals(1, Domain.objects.count())
        self.assertEquals(1, Certificate.objects.count())
        self.assertEquals(1, Connection.objects.count())

    def test_Ike2EapForm_post(self):
        url = '/connection/create/2'
        self.client.post(url, {'gateway': "gateway", 'profile': 'profile', 'username': "username", 'password': "password"})
        self.assertEquals(1, Connection.objects.count())
