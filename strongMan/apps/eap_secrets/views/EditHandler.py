from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.db.models import ProtectedError

from ..forms import AddOrEditForm


class EditHandler:
    def __init__(self, request, secret):
        self.form = None
        self.request = request
        self.secret = secret

    def _render_edit(self, form=AddOrEditForm()):
        return render(self.request, 'eap_secrets/edit.html', {"form": form, "username": self.secret.username})

    def delete_secret(self):
        try:
            self.secret.delete()
        except ProtectedError as e:
            messages.add_message(self.request, messages.ERROR,
                                 'Secret not deleted! Secret is referenced by an Connection')
            return self._render_edit(self.request)
        messages.add_message(self.request, messages.SUCCESS, 'Successfully deleted EAP Secret')
        return redirect(reverse("eap_secrets:overview"))

    def update_secret(self):
        self.form = AddOrEditForm(self.request.POST)
        if not self.form.is_valid():
            messages.add_message(self.request, messages.ERROR, 'Form was not valid')
            return self._render_edit(self.request)
        else:
            self.secret.eap_username = self.form.my_username
            self.secret.data = self.form.my_password
            self.secret.save()
            messages.add_message(self.request, messages.SUCCESS, 'Successfully updated EAP Secret')
            return redirect(reverse("eap_secrets:overview"))

    def handle(self):
        if self.request.method == "GET":
            return self._render_edit(self.request)
        elif self.request.method == "POST":
            if "remove_secret" in self.request.POST:
                return self.delete_secret()
            else:
                return self.update_secret()
