from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.db.models import ProtectedError

from ..forms import AddOrEditForm
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper


class EditHandler:
    def __init__(self, request, secret):
        self.request = request
        self.secret = secret

    def _render_edit(self, form=AddOrEditForm()):
        return render(self.request, 'eap_secrets/edit.html', {"form": form})

    def delete_secret(self):
        try:
            self.secret.delete()
        except ProtectedError as e:
            messages.add_message(self.request, messages.ERROR,
                                 'Secret not deleted! Secret is referenced by a Connection')
            return redirect(reverse("eap_secrets:overview"))
        messages.add_message(self.request, messages.SUCCESS, 'Successfully deleted EAP Secret')
        return redirect(reverse("eap_secrets:overview"))

    def update_secret(self):
        form = AddOrEditForm(self.request.POST)
        if not form.is_valid():
            return self._render_edit(form)
        else:
            self.secret.password = form.my_password
            self.secret.save()
            vici = ViciWrapper()
            # vici.clear_creds()
            vici.load_secret(self.secret.dict())
            messages.add_message(self.request, messages.SUCCESS, 'Successfully updated EAP Secret')
            return redirect(reverse("eap_secrets:overview"))

    def handle(self):
        if self.request.method == "GET":
            form = AddOrEditForm()
            form.my_username = self.secret.username
            form.my_password = self.secret.password
            return self._render_edit(form)
        elif self.request.method == "POST":
            if "remove_secret" in self.request.POST:
                return self.delete_secret()
            else:
                return self.update_secret()
