from django.contrib import messages

from ..forms import AddForm
from ..services import AddEapSecretResult


class AddHandler:
    def __init__(self, is_add_form=False):
        self.form = None
        self.request = None
        self.is_add_form = is_add_form

    @classmethod
    def by_request(cls, request, is_add_form=False):
        handler = cls(is_add_form)
        handler.request = request
        return handler

    def _render(self, form=AddForm()):
            return self.request, 'eap_secrets/overview.html', {"form": form}

    def handle(self):
        self.form = AddForm(self.request.POST)
        if not self.form.is_valid():
            messages.add_message(self.request, messages.ERROR,
                                 'Form was not valid')

        return self._render(form=self.form)

