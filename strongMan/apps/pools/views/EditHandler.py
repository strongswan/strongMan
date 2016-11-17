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
        self.pool = Pool.objects.get(poolname=self.poolname)

    def handle(self):
        if self.request.method == "GET":  # Edit
            form = AddOrEditForm()
            form.fill(self.pool)
            return render(self.request, 'pools/edit.html', {"form": form})

        elif self.request.method == "POST":
            self.form = AddOrEditForm(self.parameter_dict)
            vici = ViciWrapper()
            if "remove_pool" in self.request.POST:
                vici_poolname = {'name': self.poolname}
                try:
                    vici.unload_pool(vici_poolname)
                    self.pool.delete()
                    messages.add_message(self.request, messages.SUCCESS, "Pool deletion successful.")

                except ViciException:
                    messages.add_message(self.request, messages.ERROR,
                                         'Unload pool failed. (ViciException). There could be online leases.')
                except ProtectedError:
                    messages.add_message(self.request, messages.ERROR,
                                         'Pool not deleted. Pool is in use by a connection.')
                except Exception as e:
                    messages.add_message(self.request, messages.ERROR, str(e))
                return redirect(reverse("pools:index"))

            if not self.form.is_valid():
                messages.add_message(self.request, messages.ERROR,
                                     'Form was not valid')
                return render(self.request, 'pools/edit.html', {"form": self.form})
            else:
                self.form.update_pool(self.pool)
                try:
                    self.pool.save()
                    if self.form.my_attribute == 'None':
                        vici_pool = { self.form.my_poolname: {'addrs': self.form.my_addresses}}
                        messages.add_message(self.request, messages.SUCCESS, 'Successfully updated pool, '
                                                                             'but Attributevalue(s) not set. '
                                                                             '(Attribute was "None")')
                        vici.load_pool(vici_pool)
                        return redirect(reverse("pools:index"))
                    else:
                        vici_pool = {'name': self.form.my_poolname, 'items':
                            {'addrs': self.form.my_addresses, self.form.my_attribute: [self.form.my_attributevalues]}}
                        vici.load_pool(vici_pool)
                except IntegrityError:
                    messages.add_message(self.request, messages.ERROR,
                                         'Poolname already in use.')
                    return render(self.request, 'pools/edit.html', {"form": self.form})
                messages.add_message(self.request, messages.SUCCESS, 'Successfully updated pool')
                return redirect(reverse("pools:index"))

    @property
    def parameter_dict(self):
        parameters = self.request.POST.copy()
        parameters['poolname'] = self.poolname
        return parameters
