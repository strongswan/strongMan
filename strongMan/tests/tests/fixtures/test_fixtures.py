from django.contrib.auth import authenticate
from django.test import TestCase


class AuthenticationViewsTests(TestCase):
    fixtures = ['initial_data.json']

    def test_fixtures(self):
        user = authenticate(username='John', password='Lennon@1940')
        self.assertIsNotNone(user)
