from django.test import TestCase
from strongMan.apps.connections.forms import Ike2CertificateForm, Ike2EapCertificateForm, Ike2EapForm, ChooseTypeForm
from strongMan.apps.certificates.models import Identity


class ConnectionFormsTest(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.domain = Identity.factory(value="domain")
        self.domain.save()

    def test_ChooseTypeForm(self):
        form_data = {'typ':  "Ike2CertificateForm"}
        form = ChooseTypeForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_ChooseTypeForm_invalid(self):
        form_data = {'typ':  "sting"}
        form = ChooseTypeForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_Ike2CertificateForm(self):
        form_data = {'gateway': "gateway", 'profile': 'profile', 'certificate': self.domain.id}
        form = Ike2CertificateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_Ike2CertificateForm_invalid(self):
        form_data = {'gateway': "gateway", 'profile': 'profile'}
        form = Ike2CertificateForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_Ike2EapCertificateForm(self):
        form_data = {'gateway': "gateway", 'username': "username", 'password': 'password', 'profile': 'profile', 'certificate': self.domain.id}
        form = Ike2EapCertificateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_Ike2EapForm(self):
        form_data = {'gateway': "gateway", 'username': "username", 'password': 'password', 'profile': 'profile'}
        form = Ike2EapForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_Ike2EapForm_invalid(self):
        form_data = {'gateway': "gateway", 'username': "username", 'password': 'password'}
        form = Ike2EapForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_Ike2EapCertificateForm_invalid(self):
        form_data = {'gateway': "gateway", 'username': "username", 'password': 'password', 'profile': 'profile'}
        form = Ike2EapCertificateForm(data=form_data)
        self.assertFalse(form.is_valid())