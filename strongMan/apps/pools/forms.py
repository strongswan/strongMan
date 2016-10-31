from django import forms


class AddOrEditForm(forms.Form):
    poolname = forms.CharField(max_length=50, initial="")
    addresses = forms.CharField(max_length=150, initial="")

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
