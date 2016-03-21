import socket
from strongMan.apps.vici import vici


class ViciWrapper:
    def __init__(self):
        self.socket = socket.socket(socket.AF_UNIX)
        self.session = vici.Session(self.socket)
        self._connect_socket()

    def _connect_socket(self):
        self.socket.connect("/var/run/charon.vici")

    def load_connection(self, connection):
        '''
        :type connection: dict
        '''
        self.session.load_conn(connection)

    def unload_connection(self, connection_name):
        '''
        :type connection_name: dict
        '''
        self.session.unload_conn(connection_name)

    def load_secret(self, secret):
        '''
        :type secret: dict
        '''
        self.session.load_shared(secret)

    def load_certificate(self, certificate):
        '''
        :type certificate: dict
        '''
        self.session.load_cert(certificate)