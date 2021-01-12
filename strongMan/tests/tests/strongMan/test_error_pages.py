from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from strongMan.apps import views


class ErrorPageViewsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.request.user = self.user

    def test_400(self):
        response = views.bad_request(self.request)
        self.assertEqual(response.status_code, 400)

    def test_403(self):
        response = views.permission_denied(self.request)
        self.assertEqual(response.status_code, 403)

    def test_404(self):
        response = views.page_not_found(self.request)
        self.assertEqual(response.status_code, 404)

    def test_500(self):
        response = views.server_error(self.request)
        self.assertEqual(response.status_code, 500)
