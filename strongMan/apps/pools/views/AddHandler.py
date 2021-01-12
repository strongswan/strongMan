from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from ..models import Pool
from ..forms import AddOrEditForm
from django.db import IntegrityError
from strongMan.helper_apps.vici.wrapper.exception import ViciException
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper
from django.shortcuts import render


class AddHandler(object):
    def __init__(self, is_add_form=False):
        self.form = None
        self.request = None
        self.is_add_form = is_add_form

    @classmethod
    def by_request(cls, request, is_add_form=False):
        handler = cls(is_add_form)
        handler.request = request
        return handler

    def _render(self, form):
        if self.is_add_form:
            return render(self.request, 'pools/add_form.html', {"form": form})
        else:
            return render(self.request, 'pools/add.html', {"form": form})

    def handle(self):
        self.form = AddOrEditForm(self.request.POST)
        if not self.form.is_valid():
            return self._render(self.form)

        if self.form.my_poolname.lower() == 'dhcp' or self.form.my_poolname.lower() == 'radius':
            messages.add_message(self.request, messages.ERROR,
                                 'Poolname "' + self.form.my_poolname + '" not allowed in pool creation. To '
                                 'use this name, please reference it directly from the connection wizard.')
            return self._render(self.form)

        else:
            if self.form.my_attribute == 'None':
                if self.form.my_attributevalues != "":
                    messages.add_message(self.request, messages.ERROR,
                                         'Can\'t add pool: Attribute values unclear for Attribute "None"')
                    return self._render(self.form)
                pool = Pool(poolname=self.form.my_poolname, addresses=self.form.my_addresses)
                vici_pool = {self.form.my_poolname: {'addrs': self.form.my_addresses}}
            else:
                if self.form.my_attributevalues == "":
                    messages.add_message(self.request, messages.ERROR,
                                         'Can\'t add pool: Attribute values mandatory if attribute is set.')
                    return self._render(self.form)
                attr = self.form.my_attribute
                pool = Pool(poolname=self.form.my_poolname, addresses=self.form.my_addresses,
                            attribute=attr,
                            attributevalues=self.form.my_attributevalues)
                vici_pool = {self.form.my_poolname: {'addrs': self.form.my_addresses,
                                                     attr: [self.form.my_attributevalues]}}
        try:
            pool.clean()
            pool.save()
            vici = ViciWrapper()
            vici.load_pool(vici_pool)

        except ViciException as e:
            messages.add_message(self.request, messages.ERROR, str(e))
            pool.delete()
            return self._render(self.form)
        except IntegrityError:
            messages.add_message(self.request, messages.ERROR,
                                 'Poolname already in use.')
            return self._render(self.form)

        messages.add_message(self.request, messages.SUCCESS, 'Successfully added pool')
        if self.is_add_form:
            return render(self.request, 'pools/add_form.html', {"form": AddOrEditForm()})
        else:
            return redirect(reverse("pools:index"))
