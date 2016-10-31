from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.shortcuts import render

from ..forms import AddOrEditForm
from ...server_connections.models import Secret


class EditHandler:
    def __init__(self, request, pool):
        self.form = None
        self.request = request
        self.pool = pool

    def _render(self, form=AddOrEditForm()):
        return render(self.request, 'pools/edit.html', {"form": form, "poolname": self.pool.poolname})

    def handle(self):
        if self.request.method == "GET":  # Edit
            return self._render(self.request)

        elif self.request.method == "POST":
            if "remove_pool" in self.request.POST:
                self.pool.delete()
                return redirect(reverse("pools:index"))

            self.form = AddOrEditForm(self.request.POST)
            if not self.form.is_valid():
                messages.add_message(self.request, messages.ERROR,
                                     'Form was not valid')

            return redirect(reverse("pools:index"))


