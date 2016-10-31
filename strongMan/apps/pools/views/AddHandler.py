from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from ..models.pools import Pool
from ..forms import AddForm


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
            return self.request, 'pools/overview.html', {"form": form}

    def handle(self):
        self.form = AddForm(self.request.POST)
        if not self.form.is_valid():
            messages.add_message(self.request, messages.ERROR,
                                 'Form was not valid')
#
        pool = Pool(poolname=self.form.my_poolname, addresses=self.form.my_addresses)
        pool.save()
        return redirect(reverse("pools:index"))

