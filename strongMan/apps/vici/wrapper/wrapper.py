import socket
from .exception import ViciSocketException, ViciLoadException
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
            raise ViciLoadException("Connection cannot be loaded!") from e

    def unload_connection(self, connection_name):
        '''
        :type connection_name: dict
        '''
        self.session.unload_conn(connection_name)

    def load_secret(self, secret):
        '''
        :type secret: dict
        '''
        try:
            self.session.load_shared(secret)
        except Exception as e:
            raise ViciLoadException("Secret cannot be loaded!") from e

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
            certificates += certificate
        return certificates

    def is_connection_active(self, connection_name):
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
