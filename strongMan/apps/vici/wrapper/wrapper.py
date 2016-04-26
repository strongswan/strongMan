import socket
from collections import OrderedDict
from .exception import ViciSocketException, ViciTerminateException, ViciLoadException, ViciInitiateException
from strongMan.apps.vici import vici


class ViciWrapper:
    def __init__(self, socket_path="/var/run/charon.vici"):
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket_path = socket_path
        self.session = vici.Session(self.socket)
        self._connect_socket()

    def _connect_socket(self):
        try:
            self.socket.connect(self.socket_path)
        except Exception as e:
            raise ViciSocketException("Vici is not reachable!") from e

    def load_connection(self, connection):
        '''
        :type connection: dict
        '''
        try:
            self.session.load_conn(connection)
        except Exception as e:
            print(e)
            raise ViciLoadException("Connection cannot be loaded!") from e

    def unload_connection(self, connection_name):
        '''
        :type connection_name: str
        '''
        self.session.unload_conn(OrderedDict(name=connection_name))

    def load_secret(self, secret):
        '''
        :type secret: dict
        '''
        try:
            self.session.load_shared(secret)
        except Exception as e:
            raise ViciLoadException("Secret cannot be loaded!") from e

    def load_key(self, key):
        '''
        :type secret: dict
        '''
        try:
            self.session.load_key(key)
        except Exception as e:
            raise ViciLoadException("Private key cannot be loaded!") from e


    def load_certificate(self, certificate):
        '''
        :type certificate: dict
        '''

        try:
            self.session.load_cert(certificate)
        except Exception as e:
            raise ViciLoadException("Certificate cannot be loaded!") from e

    def get_connections_names(self):
        '''
        :return:  connection names
        :rtype: list
        '''
        connections = []
        for connection in self.session.list_conns():
            connections += connection
        return connections

    def unload_all_connections(self):
        for connection in self.get_connections_names():
            self.unload_connection(connection)

    def get_certificates(self):
        '''
        :return: certificates
         :rtype: list
        '''
        certificates = []
        for certificate in self.session.list_certs():
            certificates.append(certificate)
        return certificates

    def is_connection_loaded(self, connection_name):
        '''
        :param connection_name:
        :type connection_name: str
        :return: connection active
        :rtype: bool
        '''
        for connection in self.get_connections_names():
            if connection == connection_name:
                return True
        return False

    def is_connection_established(self, connection_name):
        return True if self.get_sas_by(connection_name) else False

    def get_version(self):
        '''
        :rtype: dict
        '''
        try:
            return self.session.version()
        except Exception as e:
            raise ViciLoadException("Version information cannot be loaded!") from e

    def get_status(self):
        try:
            return self.session.stats()
        except Exception as e:
            raise ViciLoadException("Status information cannot be loaded!") from e

    def get_plugins(self):
        '''
        :rtype: dict
        '''
        return self.get_status()['plugins']

    def get_sas(self):
        sas = []
        for sa in self.session.list_sas():
            sas.append(sa)
        return sas

    def get_sas_by(self, connection_name):
        sas = []
        for sa in self.get_sas():
            if connection_name in sa:
                sas.append(sa)
        return sas

    def initiate(self, child_name, connection_name):
        '''
        :param child_name, connection_name:
        :type child_name: str
        :type ike_name: str
        :return: log
        :rtype: List OrderedDict
        '''
        sa = OrderedDict(ike=connection_name, child=child_name)
        try:
            logs = self.session.initiate(sa)
            report = []
            for log in logs:
                report.append(log)
        except Exception as e:
            raise ViciInitiateException("SA can't be initiated!") from e
        return report

    def terminate_connection(self, connection_name):
        '''
        :param connection_name:
        :type connection_name: str
        '''
        ike = OrderedDict(ike=connection_name)
        try:
            logs = self.session.terminate(ike)
            report = []
            for log in logs:
                report.append(log)
        except Exception as e:
            raise ViciTerminateException("Cant't terminate connection " + connection_name + "!") from e
        return report
