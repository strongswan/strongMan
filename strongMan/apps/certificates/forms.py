from django import forms
from .container import ContainerDetector, ContainerTypes
from .container import X509Container, PKCS1Container, PKCS8Container, PKCS12Container
from django.contrib import messages

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


class AddHandler:
    def __init__(self):
        self.form = None
        self.request = None

    @classmethod
    def by_request(cls, request):
        handler = cls()
        handler.request = request
        return handler

    def handle(self):
        '''
        Handles a Add Container request. Adds the specific container to the database
        :return: a rendered site specific for the request
        '''
        self.form = AddForm(self.request.POST, self.request.FILES)
        if not self.form.is_valid():
            messages.add_message(self.request, messages.ERROR, 'No valid container detected. Maybe your container needs a password?')
            return (self.request, 'certificates/add.html', {"form": self.form})

        try:
            type = self.form.detect_container_type()
            if type == ContainerTypes.X509:
                return self._handle_x509()

            elif type == ContainerTypes.PKCS1 or type == ContainerTypes.PKCS8:
                return self._handle_privatekey()

            elif type == ContainerTypes.PKCS12:
                return self._handle_pkcs12()
        except Exception as e:
            messages.add_message(self.request, messages.ERROR, "Error reading file. Maybe your file is corrupt?")
            return (self.request, 'certificates/add.html', {"form": self.form})



    def _handle_x509(self):
        x509 = self.form.to_publickey()
        if x509.already_exists():
            messages.add_message(self.request, messages.WARNING, 'Certificate ' + x509.subject.cname + ' has already existed!')
        else:
            x509.save_new()
        return (self.request, 'certificates/added.html', {"public": x509})

    def _handle_privatekey(self):
        private = self.form.to_privatekey()
        public = private.publickey()
        if public == None:
            messages.add_message(self.request, messages.Error, 'No certificate exists for this private key. Upload certificate first!')
            return (self.request, 'certificates/add.html')

        if private.already_exists():
            messages.add_message(self.request, messages.WARNING, 'Private key has already existed!')
        else:
            private.save_new(public)
        return (self.request, 'certificates/added.html', {"private": private, "public": public})

    def _handle_pkcs12(self):
        private = self.form.to_privatekey()
        public = self.form.to_publickey()
        further_publics = self.form.further_publics()

        if public.already_exists():
            messages.add_message(self.request, messages.WARNING, 'Certificate ' + public.subject.cname + ' has already existed!')
        else:
            public.save_new()

        if private.already_exists():
            messages.add_message(self.request, messages.WARNING, 'Private key has already existed!')
        else:
            public = private.publickey()
            private.save_new(public)

        for cert in further_publics:
            if cert.already_exists():
                messages.add_message(self.request, messages.WARNING, 'Certificate ' + cert.subject.cname + ' has already existed!')
            else:
                cert.save_new()

        return (self.request, 'certificates/added.html', {"private": private, "public": public, "further_publics": further_publics})



