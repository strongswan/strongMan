from strongMan.apps.vici.wrapper.exception import ViciLoadException

from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper


class ServerViciWrapper(ViciWrapper):

    def get_version_pro(self):
        '''
        :rtype: dict
        '''
        try:
            return self.session.version()
        except Exception as e:
            raise ViciLoadException("Version information cannot be loaded!")

    def list_conns(self):
        connections = []
        for connection in self.session.list_conns():
            connections.append(connection)
        return connections

    def get_conns(self):
        return self.session.get_conns()

    def list_certs(self):
        certificates = []
        for certificate in self.session.list_certs():
            certificates.append(certificate)
        return certificates
