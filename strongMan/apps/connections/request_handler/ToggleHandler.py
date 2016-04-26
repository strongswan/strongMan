from django.http import JsonResponse

from strongMan.apps.vici.wrapper.exception import ViciExceptoin
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper

from ..models import Connection, State


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
            state = vici_wrapper.get_connection_state(connection.profile)
            if state == State.DOWN.value:
                connection.start()
            elif state == State.ESTABLISHED.value:
                connection.stop()
            elif state == State.CONNECTING.value:
                connection.stop()
            response['success'] = True
        except ViciExceptoin as e:
            response['message'] = str(e)
        finally:
            return JsonResponse(response)

