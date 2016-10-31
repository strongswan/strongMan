from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from ..forms import AddOrEditForm
from ...server_connections.models import Secret


class AddHandler:
    def __init__(self):
        self.form = None
        self.request = None

    @classmethod
    def by_request(cls, request):
        handler = cls()
        handler.request = request
        return handler

    def handle(self):
        self.form = AddOrEditForm(self.request.POST)
        if not self.form.is_valid():
            messages.add_message(self.request, messages.ERROR,
                                 'Form was not valid')

        secret = Secret(eap_username=self.form.my_username, type='EAP', data=self.form.my_password)
        secret.save()
        return redirect(reverse("eap_secrets:overview"))

