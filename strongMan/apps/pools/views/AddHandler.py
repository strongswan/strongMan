from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from ..models import Pool
from ..forms import AddOrEditForm
from django.db import IntegrityError


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

    def _render(self, form=AddOrEditForm()):
            return self.request, 'pools/overview.html', {"form": form}

    def handle(self):
        self.form = AddOrEditForm(self.request.POST)
        if not self.form.is_valid():
            messages.add_message(self.request, messages.ERROR,
                                 'Form was not valid')

        if not self.form.my_addresses:
            messages.add_message(self.request, messages.ERROR,
                                 'Addresses must not be empty.')
            return self._render(self.request)

        pool = Pool(poolname=self.form.my_poolname, addresses=self.form.my_addresses)
        try:
            pool.clean()
            pool.save()
        except IntegrityError:
            messages.add_message(self.request, messages.ERROR,
                                 'Poolname already in use.')
            return redirect(reverse("pools:add"))

        # load_pool -> daemon
        messages.add_message(self.request, messages.SUCCESS, 'Successfully added pool')
        return redirect(reverse("pools:index"))

