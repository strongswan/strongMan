from collections import OrderedDict
from django.shortcuts import render
from django.contrib import messages

from strongMan.apps.vici.wrapper.exception import ViciLoadException
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper


class ProHandler:
    def __init__(self, request):
        self.request = request

    def handle(self):
        if self.request.method == "GET":
            return self._render()

    def _render(self):
        context = OrderedDict()
        try:
            vici_wrapper = ViciWrapper()
            context = vici_wrapper.get_version()
        except ViciLoadException as e:
            messages.warning(self.request, str(e))
        return render(self.request, 'promode/overview.html', context)
