from django import forms


ATTRIBUTE_CHOICES = (
    ('dns', 'dns'),
    ('nbns', 'nbns'),
    ('dhcp', 'dhcp'),
    ('netmask', 'netmask'),
    ('server', 'server'),
    ('subnet', 'subnet'),
    ('split_include', 'split_include'),
    ('split_exclude', 'split_exclude'),
)


class AddOrEditForm(forms.Form):
    poolname = forms.CharField(max_length=50, initial="")
    addresses = forms.CharField(max_length=50, initial="")
    attribute = forms.ChoiceField(widget=forms.Select(), choices=ATTRIBUTE_CHOICES, label="")
    attributevalues = forms.CharField(max_length=50, initial="")

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
        return self.cleaned_data["attributevalues"]

    @my_attributevalues.setter
    def my_attributevalues(self, value):
        self.initial['attributevalues'] = value
