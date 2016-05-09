from django.http import JsonResponse

from strongMan.apps.vici.wrapper.exception import ViciExceptoin
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper

from strongMan.apps.connections.models.connections import Connection


class StateHandler:
    def __init__(self, request, id):
        self.request = request
        self.id = id

    @property
    def connection(self):
        return Connection.objects.get(pk=self.id).subclass()

    def handle(self):
        response = dict(id=self.connection.id, success=False)
        try:
            vici_wrapper = ViciWrapper()
            state = vici_wrapper.get_connection_state(self.connection.profile)
            response['state'] = state
            response['success'] = True
        except ViciExceptoin as e:
            response['message'] = str(e)
        finally:
            return JsonResponse(response)
