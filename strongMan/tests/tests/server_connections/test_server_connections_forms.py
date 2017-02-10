import os

from django.test import TestCase

from strongMan.apps.certificates.models import Certificate
from strongMan.apps.certificates.services import UserCertificateManager
from strongMan.apps.pools.models.pools import Pool
from strongMan.apps.server_connections.forms.ConnectionForms import ChooseTypeForm, Ike2CertificateForm, Ike2EapForm, \
    Ike2EapCertificateForm
from strongMan.apps.server_connections.forms.SubForms import RemoteCertificateForm, RemoteIdentityForm, HeaderForm, \
    ServerCertificateForm
from strongMan.apps.server_connections.models import IKEv2Certificate, Child, Proposal, Address, EapAuthentication, \
    CertificateAuthentication, CaCertificateAuthentication, Connection

from strongMan.tests.tests.certificates.certificates import TestCertificates

class ConnectionFormsTest(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        connection = IKEv2Certificate(profile='rw', version='1', send_certreq=False, enabled=True)
        connection.save()

        child1 = Child(name='all', mode='TUNNEL', connection=connection)
        child1.save()
        child2 = Child(name='child_2', mode='TUNNEL', connection=connection)
        child2.save()

        Proposal(type='aes128gcm128-ntru128', connection=connection).save()
        Proposal(type='aes128gcm128-ecp256', connection=connection).save()

        Address(value='127.0.0.1', local_ts=child1, remote_ts=child1, local_addresses=connection).save()
        Address(value='127.0.0.2', local_ts=child2, remote_ts=child2, remote_addresses=connection).save()

        bytes = TestCertificates.X509_googlecom.read()
        manager = UserCertificateManager()
        manager.add_keycontainer(bytes)
        manager.add_keycontainer(TestCertificates.X509_rsa_ca.read())
        manager.add_keycontainer(TestCertificates.PKCS1_rsa_ca.read())

        self.certificate = Certificate.objects.first().subclass()
        self.usercert = Certificate.objects.get(pk=2)

        self.identity = self.certificate.identities.first()

        auth = EapAuthentication(name='local-eap', auth='eap-ttls', local=connection, round=2)
        auth.save()
        CaCertificateAuthentication(name='remote-1', auth='pubkey',
                                    ca_cert=self.certificate, ca_identity="adsfasdf", remote=connection).save()
        CertificateAuthentication(name='local-1', identity=self.certificate.identities.first(), auth='pubkey', remote=connection,
                                  local=connection).save()
        connection.refresh_from_db()
        self.connection = IKEv2Certificate.objects.first()




    # @staticmethod
    # def create_connection():
    #     connection = IKEv2Certificate(profile='rw', version='1', send_certreq=False, enabled=True)
    #     connection.save()
    #
    #     child1 = Child(name='all', mode='TUNNEL', connection=connection)
    #     child1.save()
    #     child2 = Child(name='child_2', mode='TUNNEL', connection=connection)
    #     child2.save()
    #
    #     Proposal(type='aes128gcm128-ntru128', connection=connection).save()
    #     Proposal(type='aes128gcm128-ecp256', connection=connection).save()
    #
    #     Address(value='127.0.0.1', local_ts=child1, remote_ts=child2, local_addresses=connection).save()
    #     Address(value='127.0.0.2', local_ts=child1, remote_ts=child2, remote_addresses=connection).save()
    #
    #     bytes = TestCertificates.X509_googlecom.read()
    #     manager = UserCertificateManager()
    #     manager.add_keycontainer(bytes)
    #
    #     certificate = Certificate.objects.first().subclass()
    #     auth = EapAuthentication(name='local-eap', auth='eap-ttls', local=connection, round=2)
    #     auth.save()
    #     CaCertificateAuthentication(name='remote-1', auth='pubkey',
    #                                 ca_cert=certificate, ca_identity="adsfasdf", remote=connection).save()
    #     CertificateAuthentication(name='local-1', identity=certificate.identities.first(), auth='pubkey', remote=connection,
    #                               local=connection).save()
    #     connection.refresh_from_db()
    #     connection2 = Connection.objects.first()
    #     x = connection2.server_children.first().server_remote_ts.first().value
    #     return connection2

    def test_ChooseTypeForm(self):
        form_data = {'current_form': "ChooseTypeForm", 'form_name': "Ike2CertificateForm"}
        form = ChooseTypeForm(form_data, 'remote_access')
        self.assertTrue(form.is_valid())

    def test_ChooseTypeForm_invalid(self):
        form_data = {'current_form': "ChooseTypeForm", 'form_name': "string"}
        form = ChooseTypeForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_ConnectionForm_server_as_caidentity(self):
        form_data = {'current_form': Ike2CertificateForm, 'profile': 'profile',
                     'identity': self.usercert.identities.first().pk,
                     'certificate': self.usercert.pk, 'certificate_ca': self.certificate.pk, 'is_server_identity': True,
                     "version": "2", "local_addrs": '127.0.0.1', "remote_addrs": '127.0.0.2'}
        form = Ike2CertificateForm(data=form_data)
        form.update_certificates()
        self.assertTrue(form.is_valid())

    def test_ConnectionForm_server_as_caidentity_unchecked(self):
        form_data = {'current_form': Ike2CertificateForm, 'profile': 'profile',
                     'identity': self.usercert.identities.first().pk,
                     'certificate': self.usercert.pk, 'certificate_ca': self.certificate.pk, 'identity_ca': "gateway",
                     "version": "2", "local_addrs": '127.0.0.1', "remote_addrs": '127.0.0.2'}
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
        form_data = {'current_form': "Ike2EapForm",
                     'profile': 'profile', 'certificate_ca': self.certificate.pk, 'identity_ca': "yolo",
                     "version": "2", "local_addrs": '127.0.0.1', "remote_addrs": '127.0.0.2',
                     "remote_auth": 'eap-radius', 'certificate': self.usercert.pk,
                     'identity': self.usercert.subclass().identities.first().pk}
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
        form = RemoteCertificateForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.is_auto_choose)
        self.assertIsNone(form.chosen_certificate)

    def test_CaCertificateForm_is_valid2(self):
        data = {"certificate_ca": self.usercert.pk}
        form = RemoteCertificateForm(data=data)
        valid = form.is_valid()
        self.assertTrue(valid)
        self.assertFalse(form.is_auto_choose)
        self.assertIsNotNone(form.chosen_certificate)

    def test_CaCertificateForm_fill(self):
        form = RemoteCertificateForm()
        form.fill(self.connection)
        self.assertEqual(form.initial, {"certificate_ca": 1, "certificate_ca_auto": False, 'remote_auth': 'pubkey'})

    def test_CaCertificateForm_create(self):
        data = {"certificate_ca_auto": True}
        form = RemoteCertificateForm(data=data)
        self.assertTrue(form.is_valid())
        connection = IKEv2Certificate(profile='rw2', version='1', send_certreq=False, enabled=True)
        connection.save()
        form.create_connection(connection)
        newform = RemoteCertificateForm()
        newform.fill(connection)
        self.assertEqual(newform.initial, data)

    def test_CaCertificateForm_update(self):
        data = {"certificate_ca_auto": True}
        form = RemoteCertificateForm(data=data)
        self.assertTrue(form.is_valid())
        form.update_connection(self.connection)
        newform = RemoteCertificateForm()
        newform.fill(self.connection)
        self.assertEqual(newform.initial, data)

    def test_ServerIdentityForm_is_valid1(self):
        """
        Server identity checkbox is checked
        :return:
        """

        class RemoteIdentForm(HeaderForm, RemoteIdentityForm):
            pass

        data = {"current_form": "ServerIdentForm", "profile": "myNewProfileName",
                "is_server_identity": True,
                "version": "2", "local_addrs": '127.0.0.1', "remote_addrs": '127.0.0.2'}
        form = RemoteIdentForm(data=data)
        valid = form.is_valid()
        self.assertTrue(valid)
        self.assertTrue(form.is_server_identity_checked)
        self.assertEqual(form.ca_identity, '127.0.0.2')

    def test_ServerIdentityForm_is_valid2(self):
        """
        Own identity is filled
        :return:
        """

        class RemoteIdentForm(HeaderForm, RemoteIdentityForm):
            pass

        data = {"current_form": "ServerIdentForm", "profile": "myNewProfileName",
                "identity_ca": "myidentity",
                "version": "2", "local_addrs": '127.0.0.1', "remote_addrs": '127.0.0.2'}
        form = RemoteIdentForm(data=data)
        valid = form.is_valid()
        self.assertTrue(valid)
        self.assertFalse(form.is_server_identity_checked)
        self.assertEqual(form.ca_identity, "myidentity")

    def test_ServerIdentityForm_fill(self):
        form = RemoteIdentityForm()
        form.fill(self.connection)
        self.assertEqual(form.initial, {'is_server_identity': False, 'identity_ca': 'adsfasdf'})

    def test_UserCertificateForm_is_valid(self):
        data = {'certificate': self.usercert.pk, "identity": self.usercert.subclass().identities.first().pk}
        form = ServerCertificateForm(data=data)
        form.update_certificates()
        valid = form.is_valid()
        self.assertTrue(valid)
        self.assertEqual(form.my_certificate, self.usercert.subclass())
        self.assertEqual(form.my_identity, self.usercert.identities.first())

    def test_UserCertificateForm_fill(self):
        form = ServerCertificateForm()
        form.fill(self.connection)
        self.assertEqual(form.initial, {'certificate': 1, 'identity': 1})

    def test_UserCertificateForm_create(self):
        data = {'certificate': self.usercert.pk, 'identity': self.usercert.subclass().identities.first().pk}
        form = ServerCertificateForm(data=data)
        form.update_certificates()
        self.assertTrue(form.is_valid())
        pool = Pool(poolname='pool2', addresses='127.0.0.1')
        pool.save()
        connection = IKEv2Certificate(profile='rw2', version='2', pool=pool, send_certreq=False, enabled=True)
        connection.save()
        form.create_connection(connection)
        newform = ServerCertificateForm()
        newform.fill(connection)
        self.assertEqual(newform.initial, data)

    def test_UserCertificateForm_update(self):
        data = {'certificate': self.usercert.pk, 'identity': self.usercert.subclass().identities.first().pk}
        form = ServerCertificateForm(data=data)
        form.update_certificates()
        self.assertTrue(form.is_valid())
        form.update_connection(self.connection)
        newform = ServerCertificateForm()
        newform.fill(self.connection)
        self.assertEqual(newform.initial, data)

    def test_Ike2CertificateForm_is_valid(self):
        data = {"current_form": "ServerIdentForm", "profile": "myNewProfileName",
                "identity_ca": "myidentity",
                'certificate': self.usercert.pk, "identity": self.usercert.subclass().identities.first().pk,
                "certificate_ca": self.usercert.pk,
                "version": "2", "local_addrs": '127.0.0.1', "remote_addrs": '127.0.0.2'}
        form = Ike2CertificateForm(data=data)
        form.update_certificates()
        valid = form.is_valid()
        self.assertTrue(valid)

    def test_Ike2CertificateForm_fill(self):
        form = Ike2CertificateForm()
        form.fill(self.connection)
        self.assertEqual(len(form.initial), 16)

    def test_ConnectionForm_create_connection(self):
        data = {"current_form": "ServerIdentForm", "profile": "myNewProfileName",
                "identity_ca": "myidentity",
                'certificate': self.usercert.pk, "identity": self.usercert.subclass().identities.first().pk,
                "version": "2", "local_addrs": '127.0.0.1', "remote_addrs": '127.0.0.2'}

        form = Ike2CertificateForm(data)
        form.update_certificates()
        self.assertTrue(form.is_valid())
        connection = form.create_connection('remote_access')
        self.assertIsNotNone(connection)
        self.assertEqual(connection.profile, "myNewProfileName")
        self.assertEqual(connection.server_remote_addresses.first().value, '127.0.0.2')
