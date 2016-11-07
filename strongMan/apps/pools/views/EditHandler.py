from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.db import IntegrityError
from ..forms import AddOrEditForm
from strongMan.apps.pools.models import Pool


class EditHandler:
    def __init__(self, request, poolname):
        self.form = None
        self.request = request
        self.poolname = poolname

    @property
    def pool(self):
        return Pool.objects.get(poolname=self.poolname)

    def _render(self, form=AddOrEditForm()):
        if form is None:
            form = AddOrEditForm(self.pool)
            form.fill(self.pool)
        return render(self.request, 'pools/edit.html', {"form": form, "pool": self.pool})

    # , "poolname": self.pool.poolname,
    # "addresses": self.pool.addresses,
    # "attribute": self.pool.attribute,
    # "attributevalues": self.pool.attributevalues
    def handle(self):
        if self.request.method == "GET":  # Edit
            return self._render()

        elif self.request.method == "POST":
            if "remove_pool" in self.request.POST:
                self.pool.delete()
                # evtl remove/unload_pool -> daemon
                messages.add_message(self.request, messages.SUCCESS, 'Pool successfully deleted.')
                return redirect(reverse("pools:index"))

            # form = AddOrEditForm(self.request.POST)
            self.form = AddOrEditForm(self.parameter_dict)
            if not self.form.is_valid():
                messages.add_message(self.request, messages.ERROR,
                                     'Form was not valid')
                return self._render(self.request)
            else:
                # form = AddOrEditForm(self.parameter_dict)
                self.form.update_pool(self.pool)
                # self.pool.poolname = self.form.my_poolname
                # self.pool.addresses = self.form.my_addresses
                # self.pool.attribute = self.form.my_attribute
                # self.pool.attributevalues = self.form.my_attributevalues
                try:
                    self.pool.save()
                except IntegrityError:
                    messages.add_message(self.request, messages.ERROR,
                                         'Poolname already in use.')
                    return self._render(self.request)

                # load_pool -> daemon
                messages.add_message(self.request, messages.SUCCESS, 'Successfully updated pool')
                return redirect(reverse("pools:index"))

    @property
    def parameter_dict(self):
        parameters = self.request.POST.copy()
        parameters['poolname'] = self.poolname
        return parameters
