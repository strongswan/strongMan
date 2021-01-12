from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from strongMan.helper_apps.vici.wrapper.exception import ViciException
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper
from strongMan.apps.server_connections.models.specific import LogMessage

from strongMan.apps.server_connections.models import Connection


class SaTerminateHandler(object):
    def __init__(self, request):
        self.request = request
        if 'sa_id' in self.request.POST:
            self.sa_id = request.POST.get('sa_id')
        elif 'child_sa_id' in self.request.POST:
            self.child_sa_id = request.POST.get('child_sa_id')
        self.conn_id = request.POST.get('conn_id')

    def handle(self):
        try:
            connection = Connection.objects.get(id=self.conn_id).subclass()
            vici_wrapper = ViciWrapper()
            logs = None
            if hasattr(self, 'sa_id'):
                logs = vici_wrapper.terminate_ike_sa(self.sa_id)
            elif hasattr(self, 'child_sa_id'):
                logs = vici_wrapper.terminate_child_sa(self.child_sa_id)

            for log in logs:
                LogMessage(connection=connection, message=log['message']).save()

            if hasattr(self, 'sa_id'):
                messages.info(self.request, "Ike SA terminated.")
            elif hasattr(self, 'child_sa_id'):
                messages.info(self.request, "Child SA terminated.")
        except ViciException as e:
            messages.warning(self.request, str(e))

        return HttpResponseRedirect(reverse("server_connections:index"))
