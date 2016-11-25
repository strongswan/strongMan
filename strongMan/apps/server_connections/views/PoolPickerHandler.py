from django.shortcuts import render
from strongMan.apps.server_connections.forms.SubForms import PoolForm


class PoolPickerHandler:
    def __init__(self, request):
        self.request = request

    def handle(self):
        return render(self.request, 'server_connections/forms/PoolPicker.html', {"pool": PoolForm()['pool']})
