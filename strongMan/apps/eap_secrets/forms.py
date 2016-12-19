from django import forms


class EapSecretSearchForm(forms.Form):
    search_text = forms.CharField(max_length=200, required=False)


class AddOrEditForm(forms.Form):
    username = forms.RegexField(max_length=50, initial="", regex=r'^[0-9a-zA-Z_\-]+$')
    password = forms.CharField(max_length=50, widget=forms.PasswordInput, initial="")

    def is_valid(self):
        valid = super(AddOrEditForm, self).is_valid()
        return valid

    @property
    def my_username(self):
        return self.cleaned_data["username"]

    @my_username.setter
    def my_username(self, value):
        self.initial['username'] = value

    @property
    def my_password(self):
        password = self.cleaned_data["password"]
        if password == "":
            return None
        password_bytes = str.encode(password)
        return password_bytes

    @my_password.setter
    def my_password(self, value):
        self.initial['password'] = value
