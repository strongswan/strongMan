from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

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
            profilname = connection.profile
            connection.delete()
            messages.info(self.request, "Connection " + profilname + " deleted.")
            return HttpResponseRedirect(reverse("connections:index"))
