from django.test import Client, TestCase


class AuthenticationViewsTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_login_post(self):
        response = self.client.post('/auth/login/', {'username': 'John', 'password': 'Lennon'})
        self.assertEquals(response.status_code, 302)

