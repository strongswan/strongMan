from django.contrib import messages
from django.shortcuts import render

from ..models import Connection, Address
from .. import models
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper
from strongMan.apps.vici.wrapper.exception import ViciExceptoin


class OverviewHandler:
    def __init__(self, request):
        self.request = request

    def handle(self):
        try:
            self._set_connection_state()
        except ViciExceptoin as e:
            messages.warning(self.request, str(e))

        return render(self.request, 'index.html', self._get_connection_context())

    def _get_connection_context(self):
        connections = []
        for typ in Connection.get_types():
            connection_class = getattr(models, typ)
            for connection in connection_class.objects.all():
                connection_dict = dict(id=connection.id, profile=connection.profile, state=connection.state)
                address = Address.objects.filter(remote_addresses=connection).first()
                connection_dict['remote'] = address.value
                connection_dict['edit'] = "/connections/" + str(connection.id)
                connection_dict['connection_type'] = typ
                connection_dict['delete'] = "/connections/delete/" + str(connection.id)
                connections.append(connection_dict)

        return dict(connections=connections)

    def _set_connection_state(self):
        vici_wrapper = ViciWrapper()
        for connection in Connection.objects.all():
            connection.state = vici_wrapper.is_connection_established(connection.profile)
            connection.save()
