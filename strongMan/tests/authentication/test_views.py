from django.test import Client, TestCase
from django.contrib.auth.models import User


class AuthenticationViewsTests(TestCase):

    def setUp(self):
        self.client = Client()
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()

    def test_login_post(self):
        response = self.client.post('/login/', {'username': 'testuser', 'password': '12345'})
        self.assertIn('_auth_user_id', self.client.session)


