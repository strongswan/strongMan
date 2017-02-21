from django import forms


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(label='Current password', max_length=50)
    password1 = forms.CharField(label='New password', max_length=50)
    password2 = forms.CharField(label='New password again', max_length=50)

    @property
    def old_pw(self):
        return self.cleaned_data["old_password"]

    @property
    def pw1(self):
        return self.cleaned_data["password1"]

    @property
    def pw2(self):
        return self.cleaned_data["password2"]

    @property
    def error_msg(self):
        messages = []
        for key in self.errors:
            error = self.errors[key]
            label = self.fields[key].label
            msg = label + ":\n"
            for err in error:
                msg += err + "\n"
            messages.append(msg[:-1])
        return messages
