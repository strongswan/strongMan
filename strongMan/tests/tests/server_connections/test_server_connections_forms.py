import os
from django.test import TestCase
from strongMan.apps.certificates.container_reader import X509Reader, PKCS1Reader
from strongMan.apps.certificates.models import Certificate
from strongMan.apps.certificates.services import UserCertificateManager
from strongMan.apps.pools.models.pools import Pool
from strongMan.apps.server_connections.forms.ConnectionForms import ChooseTypeForm, Ike2CertificateForm, Ike2EapForm, \
    Ike2EapCertificateForm
from strongMan.apps.server_connections.forms.SubForms import CaCertificateForm, ServerIdentityForm, HeaderForm, \
    UserCertificateForm
from strongMan.apps.server_connections.models import IKEv2Certificate, Child, Proposal, Address, EapAuthentication, \
    CertificateAuthentication, CaCertificateAuthentication


class ConnectionFormsTest(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        bytes = Paths.X509_googlecom.read()
        manager = UserCertificateManager()
        manager.add_keycontainer(bytes)
        manager.add_keycontainer(Paths.X509_rsa_ca.read())
        manager.add_keycontainer(Paths.PKCS1_rsa_ca.read())

        self.certificate = Certificate.objects.first().subclass()
        self.usercert = Certificate.objects.get(pk=2)

        self.identity = self.certificate.identities.first()

    @staticmethod
    def create_connection():
        connection = IKEv2Certificate(profile='rw', version='1', send_certreq=False, enabled=True)
        connection.save()

        child1 = Child(name='all', mode='TUNNEL', connection=connection)
        child1.save()
        child2 = Child(name='child_2', mode='TUNNEL', connection=connection)
        child2.save()

        Proposal(type='aes128gcm128-ntru128', connection=connection).save()
        Proposal(type='aes128gcm128-ecp256', connection=connection).save()

        Address(value='127.0.0.1', local_ts=child1, remote_ts=child2, local_addresses=connection).save()
        Address(value='127.0.0.2', local_ts=child1, remote_ts=child2, remote_addresses=connection).save()

        bytes = Paths.X509_googlecom.read()
        manager = UserCertificateManager()
        manager.add_keycontainer(bytes)

        certificate = Certificate.objects.first().subclass()
        auth = EapAuthentication(name='local-eap', auth='eap-ttls', local=connection, round=2)
        auth.save()
        CaCertificateAuthentication(name='remote-1', auth='pubkey',
                                    ca_cert=certificate, ca_identity="adsfasdf", remote=connection).save()
        CertificateAuthentication(name='local-1', identity=certificate.identities.first(), auth='pubkey',
                                  local=connection).save()
        connection.refresh_from_db()
        return connection

    def test_ChooseTypeForm(self):
        form_data = {'current_form': "ChooseTypeForm", 'form_name': "Ike2CertificateForm"}
        form = ChooseTypeForm(form_data, 'remote_access')
        self.assertTrue(form.is_valid())

    def test_ChooseTypeForm_invalid(self):
        form_data = {'current_form': "ChooseTypeForm", 'form_name': "string"}
        form = ChooseTypeForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_ConnectionForm_server_as_caidentity(self):
        form_data = {'current_form': Ike2CertificateForm, 'gateway': "gateway", 'profile': 'profile',
                     'identity': self.usercert.identities.first().pk,
                     'certificate': self.usercert.pk, 'certificate_ca': self.certificate.pk, 'is_server_identity': True}
        form = Ike2CertificateForm(data=form_data)
        form.update_certificates()
        self.assertTrue(form.is_valid())

    def test_ConnectionForm_server_as_caidentity_unchecked(self):
        form_data = {'current_form': Ike2CertificateForm, 'gateway': "gateway", 'profile': 'profile',
                     'identity': self.usercert.identities.first().pk,
                     'certificate': self.usercert.pk, 'certificate_ca': self.certificate.pk, 'identity_ca': "gateway"}
        form = Ike2CertificateForm(data=form_data)
        form.update_certificates()
        self.assertTrue(form.is_valid())

    def test_ConnectionForm_server_as_caidentity_empty_identity_ca(self):
        form_data = {'current_form': Ike2CertificateForm, 'gateway': "gateway", 'profile': 'profile',
                     'identity': self.usercert.identities.first().pk,
                     'certificate': self.usercert.pk, 'certificate_ca': self.certificate.pk}
        form = Ike2CertificateForm(data=form_data)
        form.update_certificates()
        self.assertFalse(form.is_valid())

    def test_Ike2CertificateForm(self):
        form_data = {'gateway': "gateway", 'profile': 'profile', 'identity': self.identity.pk,
                     'certificate': self.certificate.pk}
        form = Ike2CertificateForm(data=form_data)
        # TODO Update Choices Field
        self.assertFalse(form.is_valid())

    def test_Ike2CertificateForm_invalid(self):
        form_data = {'gateway': "gateway", 'profile': 'profile'}
        form = Ike2CertificateForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_Ike2EapCertificateForm(self):
        form_data = {'gateway': "gateway", 'username': "username", 'password': 'password', 'profile': 'profile',
                     'certificate': self.identity.id}
        form = Ike2EapCertificateForm(data=form_data)
        # TODO Update Choices Field
        self.assertFalse(form.is_valid())

    def test_Ike2EapForm(self):
        form_data = {'current_form': "Ike2EapForm", 'gateway': "gateway", 'username': "username",
                     'password': 'password',
                     'profile': 'profile', 'certificate_ca': self.certificate.pk, 'identity_ca': "yolo"}
        form = Ike2EapForm(data=form_data)
        form.update_certs()
        valid = form.is_valid()
        self.assertTrue(valid)

    def test_Ike2EapForm_invalid(self):
        form_data = {'gateway': "gateway", 'username': "username", 'password': 'password'}
        form = Ike2EapForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_Ike2EapCertificateForm_invalid(self):
        form_data = {'gateway': "gateway", 'username': "username", 'password': 'password', 'profile': 'profile'}
        form = Ike2EapCertificateForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_CaCertificateForm_is_valid1(self):
        data = {"certificate_ca_auto": True}
        form = CaCertificateForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.is_auto_choose)
        self.assertIsNone(form.chosen_certificate)

    def test_CaCertificateForm_is_valid2(self):
        data = {"certificate_ca": self.usercert.pk}
        form = CaCertificateForm(data=data)
        valid = form.is_valid()
        self.assertTrue(valid)
        self.assertFalse(form.is_auto_choose)
        self.assertIsNotNone(form.chosen_certificate)

    def test_CaCertificateForm_fill(self):
        connection = self.create_connection()
        form = CaCertificateForm()
        form.fill(connection)
        self.assertEqual(form.initial, {"certificate_ca": 1, "certificate_ca_auto": False, 'remote_auth': 'pubkey'})

    def test_CaCertificateForm_create(self):
        data = {"certificate_ca_auto": True}
        form = CaCertificateForm(data=data)
        self.assertTrue(form.is_valid())
        connection = IKEv2Certificate(profile='rw2', version='1', send_certreq=False, enabled=True)
        connection.save()
        form.create_connection(connection)
        newform = CaCertificateForm()
        newform.fill(connection)
        self.assertEqual(newform.initial, data)

    def test_CaCertificateForm_update(self):
        data = {"certificate_ca_auto": True}
        form = CaCertificateForm(data=data)
        self.assertTrue(form.is_valid())
        connection = self.create_connection()
        form.update_connection(connection)
        newform = CaCertificateForm()
        newform.fill(connection)
        self.assertEqual(newform.initial, data)

    def test_ServerIdentityForm_is_valid1(self):
        """
        Server identity checkbox is checked
        :return:
        """

        class ServerIdentForm(HeaderForm, ServerIdentityForm):
            pass

        data = {"current_form": "ServerIdentForm", "profile": "myNewProfileName",
                "gateway": "LetsCallTheServerHansUeli", "is_server_identity": True}
        form = ServerIdentForm(data=data)
        valid = form.is_valid()
        self.assertTrue(valid)
        self.assertTrue(form.is_server_identity_checked)
        self.assertEqual(form.ca_identity, "LetsCallTheServerHansUeli")

    def test_ServerIdentityForm_is_valid2(self):
        """
        Own identity is filled
        :return:
        """

        class ServerIdentForm(HeaderForm, ServerIdentityForm):
            pass

        data = {"current_form": "ServerIdentForm", "profile": "myNewProfileName",
                "gateway": "LetsCallTheServerHansUeli", "identity_ca": "myidentity"}
        form = ServerIdentForm(data=data)
        valid = form.is_valid()
        self.assertTrue(valid)
        self.assertFalse(form.is_server_identity_checked)
        self.assertEqual(form.ca_identity, "myidentity")

    def test_ServerIdentityForm_fill(self):
        connection = self.create_connection()
        form = ServerIdentityForm()
        form.fill(connection)
        self.assertEqual(form.initial, {'is_server_identity': False, 'identity_ca': 'asdfasdfff'})

    def test_UserCertificateForm_is_valid(self):
        data = {'certificate': self.usercert.pk, "identity": self.usercert.subclass().identities.first().pk}
        form = UserCertificateForm(data=data)
        form.update_certificates()
        valid = form.is_valid()
        self.assertTrue(valid)
        self.assertEqual(form.my_certificate, self.usercert.subclass())
        self.assertEqual(form.my_identity, self.usercert.identities.first())

    def test_UserCertificateForm_fill(self):
        connection = self.create_connection()
        form = UserCertificateForm()
        form.fill(connection)
        self.assertEqual(form.initial, {'certificate': 1, 'identity': 1})

    def test_UserCertificateForm_create(self):
        data = {'certificate': self.usercert.pk, 'identity': self.usercert.subclass().identities.first().pk}
        form = UserCertificateForm(data=data)
        form.update_certificates()
        self.assertTrue(form.is_valid())
        connection = IKEv2Certificate(profile='rw', auth='pubkey', version=1)
        connection.save()
        form.create_connection(connection)
        newform = UserCertificateForm()
        newform.fill(connection)
        self.assertEqual(newform.initial, data)

    def test_UserCertificateForm_update(self):
        data = {'certificate': self.usercert.pk, 'identity': self.usercert.subclass().identities.first().pk}
        form = UserCertificateForm(data=data)
        form.update_certificates()
        self.assertTrue(form.is_valid())
        connection = self.create_connection()
        form.update_connection(connection)
        newform = UserCertificateForm()
        newform.fill(connection)
        self.assertEqual(newform.initial, data)

    def test_Ike2CertificateForm_is_valid(self):
        data = {"current_form": "ServerIdentForm", "profile": "myNewProfileName",
                "gateway": "LetsCallTheServerHansUeli", "identity_ca": "myidentity",
                'certificate': self.usercert.pk, "identity": self.usercert.subclass().identities.first().pk,
                "certificate_ca": self.usercert.pk}
        form = Ike2CertificateForm(data=data)
        form.update_certificates()
        valid = form.is_valid()
        self.assertTrue(valid)

    def test_Ike2CertificateForm_fill(self):
        connection = self.create_connection()
        form = Ike2CertificateForm()
        form.fill(connection)
        self.assertEqual(len(form.initial), 8)

    def test_ConnectionForm_create_connection(self):
        pool = Pool(poolname='pool', addresses='192.168.0.5').save()
        data = {"current_form": "ServerIdentForm", "profile": "myNewProfileName",
                "gateway": "LetsCallTheServerHansUeli", "identity_ca": "myidentity",
                'certificate': self.usercert.pk, "identity": self.usercert.subclass().identities.first().pk,
                "certificate_ca": self.usercert.pk, "pool": pool}

        form = Ike2CertificateForm(data)
        form.update_certificates()
        self.assertTrue(form.is_valid())
        connection = form.create_connection('remote_access')
        self.assertIsNotNone(connection)
        self.assertEqual(connection.profile, "myNewProfileName")
        self.assertEqual(connection.remote_addresses.first().value, "LetsCallTheServerHansUeli")


class TestCert:
    def __init__(self, path):
        self.path = path
        self.parent_dir = os.path.join(os.path.dirname(__file__), os.pardir)

    def read(self):
        absolute_path = self.parent_dir + "/certificates/certs/" + self.path
        with open(absolute_path, 'rb') as f:
            return f.read()

    def read_x509(self, password=None):
        bytes = self.read()
        reader = X509Reader.by_bytes(bytes, password)
        reader.parse()
        return reader

    def read_pkcs1(self, password=None):
        bytes = self.read()
        reader = PKCS1Reader.by_bytes(bytes, password)
        reader.parse()
        return reader


class Paths:
    X509_rsa_ca = TestCert("ca.crt")
    X509_rsa_ca_samepublickey_differentserialnumber = TestCert("hsrca_doppelt_gleicher_publickey.crt")
    X509_rsa_ca_samepublickey_differentserialnumber_san = TestCert("cacert_gleicher_public_anderer_serial.der")
    PKCS1_rsa_ca = TestCert("ca2.key")
    PKCS1_rsa_ca_encrypted = TestCert("ca.key")
    PKCS8_rsa_ca = TestCert("ca2.pkcs8")
    PKCS8_ec = TestCert("ec.pkcs8")
    PKCS8_rsa_ca_encrypted = TestCert("ca_enrypted.pkcs8")
    X509_rsa_ca_der = TestCert("cacert.der")
    X509_ec = TestCert("ec.crt")
    PKCS1_ec = TestCert("ec2.key")
    X509_rsa = TestCert("warrior.crt")
    PKCS12_rsa = TestCert("warrior.pkcs12")
    PKCS12_rsa_encrypted = TestCert("warrior_encrypted.pkcs12")
    X509_googlecom = TestCert("google.com_der.crt")
