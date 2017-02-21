from django import forms

from .container_reader import ContainerDetector, ContainerTypes


class CertificateSearchForm(forms.Form):
    search_text = forms.CharField(max_length=200, required=False)


class AddForm(forms.Form):
    cert = forms.FileField(label="Certificate container", required=True)
    password = forms.CharField(label="Password", max_length=60, required=False)
    cert_bytes = None

    def is_valid(self):
        valid = super(AddForm, self).is_valid()
        if not valid:
            return False
        return self.container_type() != ContainerTypes.Undefined

    def container_type(self):
        '''
        Detects the type of the uploaded Container
        :return: ContainerTypes
        '''
        password = self._read_password()
        cert_bytes = self._cert_bytes()
        detected_type = ContainerDetector.detect_type(cert_bytes, password=password)
        return detected_type

    def _cert_bytes(self):
        if self.cert_bytes is None:
            self.cert_bytes = self.cleaned_data['cert'].read()
        return self.cert_bytes

    def _read_password(self):
        password = self.cleaned_data["password"]
        if password == "":
            return None
        password_bytes = str.encode(password)
        return password_bytes


class ChangeNicknameForm(forms.Form):
    nickname = forms.CharField(max_length=100, required=True)
