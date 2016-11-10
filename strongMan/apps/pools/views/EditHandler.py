from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.db import IntegrityError
from ..forms import AddOrEditForm
from strongMan.apps.pools.models import Pool
from strongMan.helper_apps.vici.wrapper.exception import ViciException
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper
from django.db.models import ProtectedError


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

    def handle(self):
        if self.request.method == "GET":  # Edit
            return self._render()

        elif self.request.method == "POST":
            self.form = AddOrEditForm(self.parameter_dict)
            vici = ViciWrapper()
            if "remove_pool" in self.request.POST:

                vici_poolname = {'name': self.poolname}
                try:
                    success = vici.session.unload_pool(vici_poolname)
                    self.pool.delete()
                    if success:
                        messages.add_message(self.request, messages.SUCCESS,
                                             'Pool successfully deleted.')
                    else:
                        messages.add_message(self.request, messages.ERROR,
                                             'Unload pool failed.')
                except ViciException:
                    messages.add_message(self.request, messages.ERROR,
                                         'Unload pool failed. (ViciException)')
                except ProtectedError:
                    messages.add_message(self.request, messages.ERROR,
                                         'Pool not deleted. Pool is in use by a connection.')
                except Exception as e:
                    messages.add_message(self.request, messages.ERROR, str(e))
                return redirect(reverse("pools:index"))

            if not self.form.is_valid():
                messages.add_message(self.request, messages.ERROR,
                                     'Form was not valid')
                return self._render(self.request)
            else:
                self.form.update_pool(self.pool)
                try:
                    self.pool.save()
                    vici_pool = {'name': self.form.my_poolname, 'items':
                        {'addrs': self.form.my_addresses, self.form.my_attribute: [self.form.my_attributevalues]}}
                    vici.session.load_pool(vici_pool)
                except IntegrityError:
                    messages.add_message(self.request, messages.ERROR,
                                         'Poolname already in use.')
                    return self._render(self.request)
                messages.add_message(self.request, messages.SUCCESS, 'Successfully updated pool')
                return redirect(reverse("pools:index"))

    @property
    def parameter_dict(self):
        parameters = self.request.POST.copy()
        parameters['poolname'] = self.poolname
        return parameters
