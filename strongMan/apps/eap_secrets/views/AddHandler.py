from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.db import IntegrityError

from ..forms import AddOrEditForm
from ..models import Secret


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
        if self.request.method == 'GET':
            return render(self.request, 'eap_secrets/add.html', {"form": AddOrEditForm()})

        elif self.request.method == 'POST':
            self.form = AddOrEditForm(self.request.POST)
            if not self.form.is_valid():
                messages.add_message(self.request, messages.ERROR,
                                 'Form was not valid')
                return render(self.request, 'eap_secrets/add.html', {"form": AddOrEditForm()})
            else:
                try:
                    secret = Secret(username=self.form.my_username, type='EAP', password=self.form.my_password)
                    secret.save()
                except IntegrityError:
                    messages.add_message(self.request, messages.ERROR,
                                    'An EAP Secret with this Username does already exist')
                    return render(self.request, 'eap_secrets/add.html', {"form": AddOrEditForm()})

                messages.add_message(self.request, messages.SUCCESS, 'Successfully created EAP Secret')
                return redirect(reverse("eap_secrets:overview"))
