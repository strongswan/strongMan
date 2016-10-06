from strongMan.apps.vici.wrapper.wrapper import ViciWrapper
from strongMan.apps.vici.wrapper.exception import ViciLoadException


class ProViciWrapper(ViciWrapper):

    def get_version_pro(self):
        '''
        :rtype: dict
        '''
        try:
            return self.session.version()
        except Exception as e:
            raise ViciLoadException("Version information cannot be loaded!")
