from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.shortcuts import render

from ..forms import AddOrEditForm
from ...server_connections.models import Secret


class EditHandler:
    def __init__(self, request, secret):
        self.form = None
        self.request = request
        self.secret = secret

    def _render_edit(self, form=AddOrEditForm()):
        return render(self.request, 'eap_secrets/edit.html', {"form": form, "username": self.secret.eap_username})

    def handle(self):
        if self.request.method == "GET": # Edit
            return self._render_edit(self.request)

        elif self.request.method == "POST":
            if "remove_secret" in self.request.POST:
                self.secret.delete()
                messages.add_message(self.request, messages.SUCCESS, 'Successfully deleted EAP Secret')
                return redirect(reverse("eap_secrets:overview"))

            self.form = AddOrEditForm(self.request.POST)
            if not self.form.is_valid():
                messages.add_message(self.request, messages.ERROR,
                                     'Form was not valid')
                return self._render_edit(self.request)
            else:
                self.update_secret()
                messages.add_message(self.request, messages.SUCCESS, 'Successfully updated EAP Secret')
            return redirect(reverse("eap_secrets:overview"))

    def update_secret(self):
        self.secret.eap_username = self.form.my_username
        self.secret.data = self.form.my_password
        self.secret.save()

