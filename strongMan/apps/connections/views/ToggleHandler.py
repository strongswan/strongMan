from django.http import JsonResponse

from strongMan.apps.vici.wrapper.exception import ViciException
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper

from strongMan.apps.connections.models.connections import Connection
from strongMan.apps.connections.models.common import State


class ToggleHandler:
    def __init__(self, request):
        self.request = request

    def handle(self):
        connection = Connection.objects.get(id=self.request.POST['id'])
        response = dict(id=self.request.POST['id'], success=False)
        try:
            state = connection.state
            if state == State.DOWN.value:
                connection.start()
            elif state == State.ESTABLISHED.value:
                connection.stop()
            elif state == State.CONNECTING.value:
                connection.stop()
            response['success'] = True
        except ViciException as e:
            response['message'] = str(e)
        except Exception as e:
            print(e)
        finally:
            return JsonResponse(response)

