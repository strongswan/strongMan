from django import forms

from .container_reader import ContainerDetector, ContainerTypes
from .container_reader import X509Reader, PKCS1Reader, PKCS8Reader, PKCS12Reader


class CertificateSearchForm(forms.Form):
    search_text = forms.CharField(max_length=200, required=False)
    page = forms.IntegerField(max_value=99999, min_value=1)


class AddForm(forms.Form):
    cert = forms.FileField(label="Certificate container", required=True)
    password = forms.CharField(label="Password", max_length=60, required=False)
    cert_bytes = None

    def is_valid(self):
        valid = super(AddForm, self).is_valid()
        if not valid: return False
        type = self.container_type()
        return not type == ContainerTypes.Undefined

    def container_type(self):
        '''
        Detects the type of the uploaded Container
        :return: ContainerTypes
        '''
        password = self._read_password()
        cert_bytes = self._cert_bytes()
        detected_type = ContainerDetector.detect_type(cert_bytes, password=password)
        return detected_type

    def container_reader(self):
        '''
        :return: A subinstance of AbstractContainerReader
        '''
        assert self.is_valid()
        password = self._read_password()
        cert_bytes = self._cert_bytes()
        type = self.container_type()
        if type == ContainerTypes.X509:
            container = X509Reader.by_bytes(cert_bytes, password=password)
        elif type == ContainerTypes.PKCS1:
            container = PKCS1Reader.by_bytes(cert_bytes, password=password)
        elif type == ContainerTypes.PKCS8:
            container = PKCS8Reader.by_bytes(cert_bytes, password=password)
        elif type == ContainerTypes.PKCS12:
            container = PKCS12Reader.by_bytes(cert_bytes, password=password)

        container.parse()
        return container

    def _cert_bytes(self):
        if self.cert_bytes == None:
            self.cert_bytes = self.cleaned_data['cert'].read()
        return self.cert_bytes

    def _read_password(self):
        password = self.cleaned_data["password"]
        if password == "": return None
        password_bytes = str.encode(password)
        return password_bytes
