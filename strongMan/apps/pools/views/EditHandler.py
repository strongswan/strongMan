from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import render
from ..forms import AddOrEditForm
from strongMan.apps.pools.models import Pool
from strongMan.helper_apps.vici.wrapper.exception import ViciException
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper
from django.db.models import ProtectedError


class EditHandler(object):
    def __init__(self, request, poolname):
        self.form = None
        self.request = request
        self.poolname = poolname
        self.pool = Pool.objects.get(poolname=self.poolname)

    def handle(self):
        if self.request.method == "GET":
            return self.load_edit_form()

        elif self.request.method == "POST":
            self.form = AddOrEditForm(self.parameter_dict)
            vici = ViciWrapper()
            if "remove_pool" in self.request.POST:
                return self.delete_pool(vici)

            return self.update_pool(vici)

    def load_edit_form(self):
        form = AddOrEditForm()
        form.fill(self.pool)
        return render(self.request, 'pools/edit.html', {"form": form})

    def update_pool(self, vici):
        if not self.form.is_valid():
            return render(self.request, 'pools/edit.html', {"form": self.form})
        else:
            if self.form.my_attribute == 'None':
                if self.form.my_attributevalues != "":
                    messages.add_message(self.request, messages.ERROR,
                                         'Won\'t update: Attribute values unclear for Attribute "None"')
                    return render(self.request, 'pools/edit.html', {"form": self.form})
            else:
                if self.form.my_attributevalues == "":
                    messages.add_message(self.request, messages.ERROR,
                                         'Won\'t update: Attribute values mandatory if attribute is set.')
                    return render(self.request, 'pools/edit.html', {"form": self.form})
            msg = 'Successfully updated pool'

            try:
                self.form.update_pool(self.pool)
                self.pool.clean()
                vici.load_pool(self.pool.dict())
                self.pool.save()
                messages.add_message(self.request, messages.SUCCESS, msg)
            except ViciException as e:
                messages.add_message(self.request, messages.ERROR, str(e))
                return render(self.request, 'pools/edit.html', {"form": self.form})

            return redirect(reverse("pools:index"))

    def delete_pool(self, vici):
        vici_poolname = {'name': self.poolname}
        try:
            vici.unload_pool(vici_poolname)
            self.pool.delete()
            messages.add_message(self.request, messages.SUCCESS, "Pool deletion successful.")

        except ViciException as e:
            messages.add_message(self.request, messages.ERROR,
                                 'Unload pool failed: ' + str(e))
        except ProtectedError:
            messages.add_message(self.request, messages.ERROR,
                                 'Pool not deleted. Pool is in use by a connection.')
        except Exception as e:
            messages.add_message(self.request, messages.ERROR, str(e))
        return redirect(reverse("pools:index"))

    @property
    def parameter_dict(self):
        parameters = self.request.POST.copy()
        parameters['poolname'] = self.poolname
        return parameters
