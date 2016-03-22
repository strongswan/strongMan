from django import forms
from .container import ContainerDetector, ContainerTypes
from .container import X509Container, PKCS1Container, PKCS8Container, PKCS12Container
from .models import Domain

class CertificateSearchForm(forms.Form):
    search_text = forms.CharField(max_length=200)

    def search_for(self, filter_ca=False, should_CA=False):
        '''
        Searches for certificates in valid_domains
        :param filter_ca: Should result additionaly be filtered by is_CA?
        :param should_CA: Only affects the result if filter_ca=True
        :return: [Certificate]
        '''
        text = self.cleaned_data['search_text']
        domains = Domain.objects.filter(value__contains=text)
        certs = []
        for domain in domains:
            cert = domain.certificate
            if not cert in certs:
                if filter_ca:
                    if cert.is_CA == should_CA:
                        certs.append(cert)
                else:
                    certs.append(cert)
        return certs




class CommandForm(forms.Form):
    command = forms.CharField(max_length=20, required=True)



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
            container = X509Container.by_bytes(cert_bytes, password=password)
        elif type == ContainerTypes.PKCS12:
            container = PKCS12Container.by_bytes(cert_bytes, password=password)
        container.parse()
        publickey = container.to_public_key()
        return publickey

    def to_privatekey(self):
        type = self.detect_container_type()
        assert type == ContainerTypes.PKCS1 or type == ContainerTypes.PKCS8 or type == ContainerTypes.PKCS12
        password = self._read_password()
        cert_bytes = self._cert_bytes()
        if type == ContainerTypes.PKCS1:
            container = PKCS1Container.by_bytes(cert_bytes, password=password)
        elif type == ContainerTypes.PKCS8:
            container = PKCS8Container.by_bytes(cert_bytes, password=password)
        elif type == ContainerTypes.PKCS12:
            container = PKCS12Container.by_bytes(cert_bytes, password=password)

        container.parse()
        privatekey = container.to_private_key()
        return privatekey

    def further_publics(self):
        assert self.detect_container_type() == ContainerTypes.PKCS12
        password = self._read_password()
        cert_bytes = self._cert_bytes()
        container = PKCS12Container.by_bytes(cert_bytes, password=password)

        container.parse()
        publics = container.further_publics()
        return publics

    def _cert_bytes(self):
        if self.cert_bytes == None:
            self.cert_bytes = self.cleaned_data['cert'].read()
        return self.cert_bytes




