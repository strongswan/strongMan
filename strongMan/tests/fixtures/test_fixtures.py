from django.contrib.auth import authenticate
from django.test import Client, TestCase


class AuthenticationViewsTests(TestCase):
    fixtures = ['initial_data.json']

    def test_fixtures(self):
        user = authenticate(username='John', password='Lennon')
        self.assertIsNotNone(user)