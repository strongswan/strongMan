from django.contrib import messages
from django.http import HttpResponseRedirect

from strongMan.apps.vici.wrapper.exception import ViciExceptoin
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper

from ..models import Connection


class DeleteHandler:
    def __init__(self, request, id):
        self.request = request
        self.id = id

    def handle(self):
        connection = Connection.objects.get(id=self.id).subclass()
        try:
            vici_wrapper = ViciWrapper()
            if vici_wrapper.is_connection_loaded(connection.profile) is True:
                vici_wrapper.unload_connection(connection.profile)
        except ViciExceptoin as e:
            messages.warning(self.request, str(e))
        finally:
            connection.delete()
            return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))
