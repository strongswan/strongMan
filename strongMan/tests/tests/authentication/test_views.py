from django.contrib.auth.models import User
from django.test import Client, TestCase

from strongMan.apps.views import PwChangeHandler


class AuthenticationViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()

    def test_login_post(self):
        response = self.client.post('/login/', {'username': 'testuser', 'password': '12345'})
        self.assertIn('_auth_user_id', self.client.session)


class PwChangeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser')
        self.user.set_password('1234')
        self.user.save()
        self.client = Client()
        response = self.client.post('/login/', {'username': 'testuser', 'password': '1234'})

    def assert_pw_not_changed(self, response):
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("1234"))
        self.assertNotContains(response, "Password changed successfully!")

    def test_pw_change_successfully(self):
        url = '/change_pw'
        response = self.client.post(url, {"old_password": "1234", "password1": "Newpassword!2",
                                          "password2": "Newpassword!2"})
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Newpassword!2"))

    def test_send_nothing(self):
        url = '/change_pw'
        response = self.client.post(url, {})
        self.assert_pw_not_changed(response)

    def test_wrong_current_pw(self):
        url = '/change_pw'
        response = self.client.post(url, {"old_password": "asfasdfa", "password1": "newpassword!",
                                          "password2": "newpassword!"})
        self.assert_pw_not_changed(response)

    def test_notequal_pw(self):
        url = '/change_pw'
        response = self.client.post(url, {"old_password": "1234", "password1": "newpassword!",
                                          "password2": "newpassword!2"})
        self.assert_pw_not_changed(response)

    def test_pw_rules(self):
        url = '/change_pw'
        response = self.client.post(url, {"old_password": "1234", "password1": "newpassword",
                                          "password2": "newpassword"})
        self.assert_pw_not_changed(response)


class AboutHandlerTest(TestCase):
    def setUp(self):
        self.handler = PwChangeHandler(None)

    def test_has_upper(self):
        self.assertFalse(self.handler._has_upper("123456"))
        self.assertFalse(self.handler._has_upper("asdfljalsdf"))
        self.assertTrue(self.handler._has_upper("asdfaWas!"))

    def test_has_lower(self):
        self.assertFalse(self.handler._has_lower("123456"))
        self.assertFalse(self.handler._has_lower("ASDFASFJASDFLR1!"))
        self.assertTrue(self.handler._has_lower("DSFFFFFFFFuLJ!"))

    def test_has_digit(self):
        self.assertFalse(self.handler._has_digit("asdfasdf"))
        self.assertFalse(self.handler._has_digit("ASDFASFJaSDFLR!"))
        self.assertTrue(self.handler._has_digit("DSFF6FFFFFuLJ!"))

    def test_is_password_hard(self):
        self.assertFalse(self.handler._is_password_hard("as8Fasd"), "Only 7 signs")
        self.assertFalse(self.handler._is_password_hard("asdfasd8"), "No upper case")
        self.assertFalse(self.handler._is_password_hard("LJSLDFJF8"), "No lower case")
        self.assertFalse(self.handler._is_password_hard("LJSLDFJF#"), "No digit")
        self.assertTrue(self.handler._is_password_hard("lkjsdfF#ddkla8"))
