from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import render
from django.db import IntegrityError

from ..forms import AddOrEditForm
from ..models import Secret
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper


class AddHandler(object):
    def __init__(self):
        self.form = None
        self.request = None

    @classmethod
    def by_request(cls, request):
        handler = cls()
        handler.request = request
        return handler

    def handle(self):
        if self.request.method == 'GET':
            return render(self.request, 'eap_secrets/add.html', {"form": AddOrEditForm()})

        elif self.request.method == 'POST':
            self.form = AddOrEditForm(self.request.POST)
            if not self.form.is_valid():
                return render(self.request, 'eap_secrets/add.html', {"form": self.form})
            else:
                try:
                    secret = Secret(username=self.form.my_username, type='EAP',
                                    password=self.form.my_salted_password, salt=self.form.my_salt)
                    secret.save()
                except IntegrityError:
                    messages.add_message(self.request, messages.ERROR,
                                         'An EAP Secret with this Username does already exist')
                    return render(self.request, 'eap_secrets/add.html', {"form": self.form})
                ViciWrapper().load_secret(secret.dict())
                messages.add_message(self.request, messages.SUCCESS, 'Successfully created EAP Secret')
                return redirect(reverse("eap_secrets:overview"))
