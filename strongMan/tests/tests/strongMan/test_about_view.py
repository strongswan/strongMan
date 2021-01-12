from django.contrib.auth.models import User
from django.test import Client, TestCase


class AboutViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.client.login(username='testuser', password='12345')

    def test_about_get(self):
        url = '/about/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
