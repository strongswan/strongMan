from django.http import JsonResponse

from strongMan.apps.vici.wrapper.exception import ViciExceptoin
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper

from ..models import Connection


class ToggleHandler:
    def __init__(self, request):
        self.request = request

    def handle(self):
        connection = Connection.objects.get(id=self.request.POST['id'])
        response = dict(id=self.request.POST['id'], success=False)
        try:
            vici_wrapper = ViciWrapper()
            if vici_wrapper.is_connection_established(self.subclass().profile) is False:
                connection.start()
            else:
                connection.stop()
            response['success'] = True
        except ViciExceptoin as e:
            response['message'] = str(e)
        finally:
            return JsonResponse(response)

