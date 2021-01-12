from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import render
from django.db.models import ProtectedError

from ..forms import AddOrEditForm
from ..models import Secret
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper
from strongMan.helper_apps.vici.wrapper.exception import ViciException


class EditHandler(object):
    def __init__(self, request, secret):
        self.request = request
        self.secret = secret

    def _render_edit(self, form=AddOrEditForm()):
        return render(self.request, 'eap_secrets/edit.html', {"form": form})

    def delete_secret(self):
        try:
            store_secret = self.secret
            self.secret.delete()
            self.reload_secrets()
            messages.add_message(self.request, messages.SUCCESS, 'Successfully deleted EAP Secret')
        except ProtectedError:
            messages.add_message(self.request, messages.ERROR,
                                 'Secret not deleted! Secret is referenced by a Connection')
        except ViciException as e:
            store_secret.save()
            messages.add_message(self.request, messages.ERROR, str(e))
        return redirect(reverse("eap_secrets:overview"))

    def update_secret(self):
        form = AddOrEditForm(self.request.POST)
        if not form.is_valid():
            return self._render_edit(form)
        else:
            try:
                store_secret = self.secret
                self.secret.password = form.my_salted_password
                self.secret.salt = form.my_salt
                self.secret.save()
                self.reload_secrets()
                messages.add_message(self.request, messages.SUCCESS, 'Successfully updated EAP Secret')
            except ViciException as e:
                store_secret.save()
                messages.add_message(self.request, messages.ERROR, str(e))
                return render(self.request, 'eap_secrets/edit.html', {"form": form})
            return redirect(reverse("eap_secrets:overview"))

    def reload_secrets(self):
        vici = ViciWrapper()
        vici.clear_creds()
        for secret in Secret.objects.all():
            vici.load_secret(secret.dict())

    def handle(self):
        if self.request.method == "GET":
            form = AddOrEditForm()
            form.my_username = self.secret.username
            form.my_salted_password = self.secret.password
            return self._render_edit(form)
        elif self.request.method == "POST":
            if "remove_secret" in self.request.POST:
                return self.delete_secret()
            else:
                return self.update_secret()
