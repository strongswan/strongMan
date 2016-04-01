from django import forms

from .container_reader import ContainerDetector, ContainerTypes
from .container_reader import X509Reader, PKCS1Reader, PKCS8Reader, PKCS12Reader
from .models import Certificate, PrivateKey, CertificateFactory

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
        type = self.detect_container_type()
        return not type == ContainerTypes.Undefined

    def detect_container_type(self):
        '''
        Detects the type of the uploaded Container
        :return: ContainerTypes
        '''
        password = self._read_password()
        cert_bytes = self._cert_bytes()
        detected_type = ContainerDetector.detect_type(cert_bytes, password=password)
        return detected_type

    def _read_password(self):
        password = self.cleaned_data["password"]
        if password == "": return None
        password_bytes = str.encode(password)
        return password_bytes

    def to_publickey(self):
        type = self.detect_container_type()
        assert type == ContainerTypes.X509 or type == ContainerTypes.PKCS12
        password = self._read_password()
        cert_bytes = self._cert_bytes()
        if type == ContainerTypes.X509:
            container = X509Reader.by_bytes(cert_bytes, password=password)
            container.parse()
        elif type == ContainerTypes.PKCS12:
            container = PKCS12Reader.by_bytes(cert_bytes, password=password)
            container.parse()
            container = container.public_key()
        return CertificateFactory.by_X509Container(container)

    def to_privatekey(self):
        type = self.detect_container_type()
        assert type == ContainerTypes.PKCS1 or type == ContainerTypes.PKCS8 or type == ContainerTypes.PKCS12
        password = self._read_password()
        cert_bytes = self._cert_bytes()
        if type == ContainerTypes.PKCS1:
            container = PKCS1Reader.by_bytes(cert_bytes, password=password)
            container.parse()
        elif type == ContainerTypes.PKCS8:
            container = PKCS8Reader.by_bytes(cert_bytes, password=password)
            container.parse()
        elif type == ContainerTypes.PKCS12:
            container = PKCS12Reader.by_bytes(cert_bytes, password=password)
            container.parse()
            container = container.private_key()


        privatekey = PrivateKey.by_pkcs1_or_8_container(container)
        return privatekey

    def further_publics(self):
        assert self.detect_container_type() == ContainerTypes.PKCS12
        password = self._read_password()
        cert_bytes = self._cert_bytes()
        container = PKCS12Reader.by_bytes(cert_bytes, password=password)

        container.parse()
        publics = container.further_publics()
        certificates = []
        for public in publics:
            cert = CertificateFactory.by_X509Container(public)
            certificates.append(cert)

        return certificates

    def _cert_bytes(self):
        if self.cert_bytes == None:
            self.cert_bytes = self.cleaned_data['cert'].read()
        return self.cert_bytes
