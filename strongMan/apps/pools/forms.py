from django import forms
from strongMan.apps.pools.models.pools import ATTRIBUTE_CHOICES


class AddOrEditForm(forms.Form):
    poolname = forms.RegexField(max_length=50, initial="", regex=r'^[0-9a-zA-Z]+$')
    addresses = forms.CharField(initial="", required=None)
    attribute = forms.ChoiceField(widget=forms.Select(), choices=ATTRIBUTE_CHOICES)
    attributevalues = forms.CharField(initial="", required=None)

    def fill(self, pool):
        self.initial['poolname'] = pool.poolname
        self.initial['addresses'] = pool.addresses
        self.initial['attribute'] = pool.attribute
        if pool.attribute is None:
            self.initial['attributevalues'] = ""
        else:
            self.initial['attributevalues'] = pool.attributevalues

    def update_pool(self, pool):
        pool.poolname = self.cleaned_data['poolname']
        pool.addresses = self.cleaned_data['addresses']
        if self.cleaned_data['attribute'] == 'None':
            pool.attribute = None
            pool.attributevalues = None
        else:
            pool.attribute = self.cleaned_data['attribute']
            pool.attributevalues = self.cleaned_data['attributevalues']
        pool.save()

    def is_valid(self):
        valid = super(AddOrEditForm, self).is_valid()
        return valid

    @property
    def my_poolname(self):
        return self.cleaned_data["poolname"]

    @my_poolname.setter
    def my_poolname(self, value):
        self.initial['poolname'] = value

    @property
    def my_addresses(self):
        return self.cleaned_data["addresses"]

    @my_addresses.setter
    def my_addresses(self, value):
        self.initial['addresses'] = value

    @property
    def my_attribute(self):
        return self.cleaned_data["attribute"]

    @my_attribute.setter
    def my_attribute(self, value):
        self.initial['attribute'] = value

    @property
    def my_attributevalues(self):
        return self.data["attributevalues"]

    @my_attributevalues.setter
    def my_attributevalues(self, value):
        self.initial['attributevalues'] = value


# class OverviewDetailForm(forms.Form):
#     base = forms.CharField(max_length=50, initial="")
#     size = forms.CharField(max_length=50, initial="")
#     online = forms.CharField(max_length=50, initial="")
#     offline = forms.CharField(max_length=50, initial="")
#     leases = forms.CharField(max_length=50, initial="")
#
#     def fill(self, pool_details):
#         self.initial['base'] = pool_details.base
#         self.initial['size'] = pool_details.size
#         self.initial['online'] = pool_details.online
#         self.initial['offline'] = pool_details.offline
#         self.initial['leases'] = pool_details.leases
#
#     @property
#     def my_base(self):
#         return self.cleaned_data["base"]
#
#     @my_base.setter
#     def my_base(self, value):
#         self.initial['base'] = value
#
#     @property
#     def my_size(self):
#         return self.cleaned_data["size"]
#
#     @my_base.setter
#     def my_size(self, value):
#         self.initial['size'] = value
#
#     @property
#     def my_online(self):
#         return self.cleaned_data["online"]
#
#     @my_online.setter
#     def my_online(self, value):
#         self.initial['online'] = value
#
#     @property
#     def my_offline(self):
#         return self.cleaned_data["offline"]
#
#     @my_offline.setter
#     def my_offline(self, value):
#         self.initial['offline'] = value
#
#     @property
#     def my_leases(self):
#         return self.cleaned_data["leases"]
#
#     @my_leases.setter
#     def my_leases(self, value):
#         self.initial['leases'] = value
