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
            raise ViciSocketException("Vici is not reachable!")

    def load_connection(self, connection):
        '''
        :type connection: dict
        '''
        try:
            self.session.load_conn(connection)
        except Exception as e:
            print(e)
            raise ViciLoadException("Connection cannot be loaded!")

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
            raise ViciLoadException("Secret cannot be loaded!")

    def load_key(self, key):
        '''
        :type secret: dict
        '''
        try:
            self.session.load_key(key)
        except Exception as e:
            raise ViciLoadException("Private key cannot be loaded!")


    def load_certificate(self, certificate):
        '''
        :type certificate: dict
        '''

        try:
            self.session.load_cert(certificate)
        except Exception as e:
            raise ViciLoadException("Certificate cannot be loaded!")

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
        except Exception as e:
            raise ViciLoadException("Version information cannot be loaded!")

    def get_status(self):
        try:
            return self.session.stats()
        except Exception as e:
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
                level = log['level'].decode('ascii')
                message = log['msg'].decode('ascii')
                yield OrderedDict(level=level, message=message)
        except Exception as e:
            raise ViciInitiateException("SA can't be initiated!")

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
            raise ViciTerminateException("Can't terminate connection " + connection_name + "!")
        return report


    def get_connection_state(self, connection_name):
        sa = self.get_sas_by(connection_name)
        if sa:
            values = sa[0][connection_name]
            state = values['state']
            return state.decode('ascii')
        else:
            return 'DOWN'

'''
[OrderedDict([('cert',
    OrderedDict([('uniqueid', b'2'),
        ('version', b'2'),
        ('state', b'ESTABLISHED'),
        ('local-host', b'172.17.0.1'),
        ('local-port', b'4500'),
        ('local-id', b'C=CH, O=Linux strongSwan, OU=Research, CN=carol@strongswan.org'),
        ('remote-host', b'172.17.0.2'),
        ('remote-port', b'4500'),
        ('remote-id', b'moon.strongswan.org'),
        ('initiator', b'yes'),
        ('initiator-spi', b'bfdd33c1a24810e2'),
        ('responder-spi', b'643537f4c01507e4'),
        ('encr-alg', b'AES_CBC'),
        ('encr-keysize', b'128'),
        ('integ-alg', b'HMAC_SHA2_256_128'),
        ('prf-alg', b'PRF_HMAC_SHA2_256'),
        ('dh-group', b'MODP_2048'),
        ('established', b'16'),
        ('rekey-time', b'13312'),
        ('local-vips', [b'10.6.0.1']),
        ('child-sas',
            OrderedDict([('cert',
                OrderedDict([('uniqueid', b'2'),
                    ('reqid', b'2'),
                    ('state', b'INSTALLED'),
                    ('mode', b'TUNNEL'),
                    ('protocol', b'ESP'),
                    ('spi-in', b'c46d302e'),
                    ('spi-out', b'c2125947'),
                    ('encr-alg', b'AES_GCM_16'),
                    ('encr-keysize', b'128'),
                    ('bytes-in', b'0'),
                    ('packets-in', b'0'),
                    ('bytes-out', b'0'),
                    ('packets-out', b'0'),
                    ('rekey-time', b'3241'),
                    ('life-time', b'3944'),
                    ('install-time', b'16'),
                    ('local-ts', [b'10.6.0.1/32']),
                    ('remote-ts', [b'172.17.0.2/32'])]))]))]))])]

[OrderedDict([('cert', OrderedDict([('uniqueid', b'1'), ('version', b'2'), ('state', b'CONNECTING'), ('local-host', b'172.17.0.1'), ('local-port', b'500'), ('local-id', b'%any'), ('remote-host', b'172.17.0.2'), ('remote-port', b'500'), ('remote-id', b'%any'), ('initiator', b'yes'), ('initiator-spi', b'10f1339048108561'), ('responder-spi', b'0000000000000000'), ('tasks-active', [b'IKE_VENDOR', b'IKE_INIT', b'IKE_NATD', b'IKE_CERT_PRE', b'IKE_AUTH', b'IKE_CERT_POST', b'IKE_CONFIG', b'CHILD_CREATE', b'IKE_AUTH_LIFETIME', b'IKE_MOBIKE']), ('child-sas', OrderedDict())]))])]


'''

