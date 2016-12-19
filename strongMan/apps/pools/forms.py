from django import forms
from strongMan.apps.pools.models.pools import ATTRIBUTE_CHOICES


class AddOrEditForm(forms.Form):
    poolname = forms.RegexField(max_length=50, initial="", regex=r'^[0-9a-zA-Z_\-]+$')
    addresses = forms.CharField(initial="")
    attribute = forms.ChoiceField(widget=forms.Select(), choices=ATTRIBUTE_CHOICES)
    attributevalues = forms.CharField(initial="", required=False)

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
