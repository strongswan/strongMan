from django.http import JsonResponse

from strongMan.apps.server_connections.models.common import State
from strongMan.apps.server_connections.models.connections import Connection
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
            elif state == State.UNLOADED.value:
                connection.load()
            elif state == State.LOADED.value:
                connection.unload()
            response['success'] = True
        except ViciException as e:
            response['message'] = str(e)
        except Exception as e:
            print(e)

        return JsonResponse(response)

    def unload(self, id):
        connection = Connection.objects.get(id=id)
        response = dict(id=id, success=False)
        try:
            state = connection.state
            if state == State.ESTABLISHED.value:
                connection.stop()
            elif state == State.LOADED.value:
                connection.unload()
            response['success'] = True
        except ViciException as e:
            response['message'] = str(e)
        except Exception as e:
            print(e)

        return JsonResponse(response)

    def load(self, id):
        connection = Connection.objects.get(id=id)
        response = dict(id=id, success=False)
        try:
            state = connection.state
            if state == State.DOWN.value:
                connection.start()
            elif state == State.UNLOADED.value:
                connection.load()
            response['success'] = True
        except ViciException as e:
            response['message'] = str(e)
        except Exception as e:
            print(e)

        return JsonResponse(response)
