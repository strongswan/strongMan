from django.contrib.auth import authenticate
from django.test import Client, TestCase


class AuthenticationViewsTests(TestCase):
    fixtures = ['data.json']

    def test_fixtures(self):
        user = authenticate(username='John', password='Lennon')
        self.assertIsNotNone(user)