import os
import socket
import stat
import vici
from collections import OrderedDict
from .exception import ViciSocketException, ViciTerminateException, ViciLoadException, \
    ViciInitiateException, ViciPathNotASocketException


class ViciWrapper(object):
    def __init__(self, socket_path="/var/run/charon.vici"):
        self.socket_path = socket_path
        if not os.path.exists(self.socket_path):
            raise ViciSocketException(self.socket_path + " doesn't exist!")
        if not self._is_path_a_socket():
            raise ViciPathNotASocketException("The path '" + self.socket_path + "' is not a Socket!")
        self._connect_socket()

    def __del__(self):
        self._close_socket()

    def _close_socket(self):
        try:
            self.socket.shutdown(2)
            self.socket.close()
        except Exception:
            pass

    def _connect_socket(self):
        try:
            self.socket = socket.socket(socket.AF_UNIX)
            self.socket.connect(self.socket_path)
            self.session = vici.Session(self.socket)
        except Exception as e:
            raise ViciSocketException("Vici is not reachable! " + str(e))

    def _is_path_a_socket(self):
        mode = os.stat(self.socket_path).st_mode
        return stat.S_ISSOCK(mode)

    def load_connection(self, connection):
        '''
        :type connection: dict
        '''
        try:
            self.session.load_conn(connection)
        except Exception as e:
            raise ViciLoadException("Connection cannot be loaded! " + str(e))

    def unload_connection(self, connection_name):
        '''
        :type connection_name: str
        '''
        if connection_name in self.get_connections_names():
            self.session.unload_conn(OrderedDict(name=connection_name))

    def load_secret(self, secret):
        '''
        :type secret: dict
        '''
        try:
            self.session.load_shared(secret)
        except Exception as e:
            raise ViciLoadException("Secret cannot be loaded! " + str(e))

    def load_key(self, key):
        '''
        :type secret: dict
        '''
        try:
            self.session.load_key(key)
        except Exception as e:
            raise ViciLoadException("Private key cannot be loaded! " + str(e))

    def load_certificate(self, certificate):
        '''
        :type certificate: dict
        '''

        try:
            self.session.load_cert(certificate)
        except Exception as e:
            raise ViciLoadException("Certificate cannot be loaded! " + str(e))

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

    def get_version(self):
        '''
        :rtype: dict
        '''
        try:
            return self.session.version()
        except Exception:
            raise ViciLoadException("Version information cannot be loaded!")

    def get_status(self):
        try:
            return self.session.stats()
        except Exception:
            raise ViciLoadException("Status information cannot be loaded!")

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
            for log in logs:
                message = log['msg'].decode('ascii')
                yield OrderedDict(message=message)
        except Exception as e:
            raise ViciInitiateException("SA can't be initiated! " + str(e))

    def terminate_connection(self, connection_name):
        '''
        :param connection_name:
        :type connection_name: str
        '''
        sa = OrderedDict(ike=connection_name)
        try:
            logs = self.session.terminate(sa)
            for log in logs:
                message = log['msg'].decode('ascii')
                yield OrderedDict(message=message)
        except Exception as e:
            raise ViciTerminateException("Can't terminate connection " + connection_name + "! " + str(e))

    def terminate_ike_sa(self, unique_sa_id):
        '''
        :param unique_sa_id:
        :type unique_sa_id: str
        '''
        ike_sa = OrderedDict()
        ike_sa['ike-id'] = unique_sa_id
        try:
            logs = self.session.terminate(ike_sa)
            for log in logs:
                message = log['msg'].decode('ascii')
                yield OrderedDict(message=message)
        except Exception as e:
            raise ViciTerminateException("Can't terminate IKE SA! " + str(e))

    def terminate_child_sa(self, reqid):
        '''
        :param reqid:
        :type reqid: str
        '''
        child_sa = OrderedDict()
        child_sa['child-id'] = reqid
        try:
            logs = self.session.terminate(child_sa)
            for log in logs:
                message = log['msg'].decode('ascii')
                yield OrderedDict(message=message)
        except Exception as e:
            raise ViciTerminateException("Can't terminate Child SA! " + str(e))

    def get_connection_state(self, connection_name):
        default_state = 'DOWN'
        try:
            sa = self.get_sas_by(connection_name)
            if sa:
                values = sa[0][connection_name]
                state = values['state']
                return state.decode('ascii')
            else:
                return default_state
        except Exception:
            return default_state

    def get_pools(self, include_leases):
        try:
            return self.session.get_pools(include_leases)
        except Exception:
            return self.session.get_pools()

    def unload_pool(self, pool_name):
        try:
            self.session.unload_pool(pool_name)
        except Exception as e:
            raise ViciLoadException(str(e))

    def clear_creds(self):
        try:
            self.session.clear_creds()
        except Exception as e:
            raise ViciLoadException("Credentials cannot be cleared! " + str(e))

    def load_pool(self, pool):
        try:
            self.session.load_pool(pool)
        except Exception as e:
            raise ViciLoadException("Pool could not be loaded! " + str(e))
