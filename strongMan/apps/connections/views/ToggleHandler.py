from django.http import JsonResponse

from strongMan.apps.connections.models.common import State
from strongMan.apps.connections.models.connections import Connection
from strongMan.helper_apps.vici.wrapper.exception import ViciException


class ToggleHandler(object):
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

        return JsonResponse(response)
