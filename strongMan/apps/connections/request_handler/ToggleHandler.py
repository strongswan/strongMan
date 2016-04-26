from django.http import JsonResponse

from strongMan.apps.vici.wrapper.exception import ViciExceptoin
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper

from ..models import Connection


class ChildSA(object):
    def __init__(self, sa, connection_name):
        sa = sa[connection_name]
        child_sas = sa['child-sas']
        child_sa = child_sas[connection_name]
        self.remote_ts = child_sa['remote-ts'][0].decode('ascii')
        self.local_ts = child_sa['local-ts'][0].decode('ascii')


class ToggleHandler:
    def __init__(self, request):
        self.request = request

    def handle(self):
        connection = Connection.objects.get(id=self.request.POST['id'])
        response = dict(id=self.request.POST['id'], success=False)
        try:
            vici_wrapper = ViciWrapper()
            if vici_wrapper.is_connection_established(connection.profile):
                connection.stop()
            else:
                connection.start()
                '''
                sas = vici_wrapper.get_sas_by(connection.profile)

                for sa in sas:
                    ChildSA(sa, connection.profile)
                '''
            response['success'] = True
        except ViciExceptoin as e:
            response['message'] = str(e)
        finally:
            return JsonResponse(response)

