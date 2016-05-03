from django.http import JsonResponse

from strongMan.apps.vici.wrapper.exception import ViciExceptoin
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper

from ..models import Connection, State


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
        except Exception as e:
            print(e)
        finally:
            return JsonResponse(response)

