from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render, HttpResponseRedirect

from .container import ContainerTypes
from .forms import AddForm


class DetailsHandler:
    def __init__(self, request, certificate_object):
        self.request = request
        self.certificate = certificate_object

    def _render_detail(self):
        if self.certificate.private_key is None:
            return render(self.request, 'certificates/edit.html', {"certificate": self.certificate})
        else:
            return render(self.request, 'certificates/edit.html',
                          {"certificate": self.certificate, 'private': self.certificate.private_key})

    def _remove_certificate(self):
        cname = self.certificate.subject.cname
        self.certificate.delete()
        return cname

    def _remove_privatekey(self):
        private = self.certificate.private_key
        self.certificate.private_key = None
        self.certificate.save()
        privatekey_has_another_certificate = private.certificates.all().__len__() > 1
        if not privatekey_has_another_certificate:
            private.delete()

    def handle(self):
        if self.request.method == "GET":
            return self._render_detail()
        elif self.request.method == "POST":
            if "remove_cert" in self.request.POST:
                cname = self._remove_certificate()
                messages.add_message(self.request, messages.INFO, "Certificate " + cname + " has been removed.")
                return HttpResponseRedirect(reverse('certificates:overview'))
            elif "remove_privatekey" in self.request.POST:
                self._remove_privatekey()
                messages.add_message(self.request, messages.INFO, "Private key has been removed.")
                return self._render_detail()
        return self._render_detail()


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
            messages.add_message(self.request, messages.ERROR,
                                 'No valid container detected. Maybe your container needs a password?')
            return self.request, 'certificates/add.html', {"form": self.form}

        try:
            type = self.form.detect_container_type()
            if type == ContainerTypes.X509:
                return self._handle_x509()

            elif type == ContainerTypes.PKCS1 or type == ContainerTypes.PKCS8:
                return self._handle_privatekey()

            elif type == ContainerTypes.PKCS12:
                return self._handle_pkcs12()
        except Exception as e:
            messages.add_message(self.request, messages.ERROR,
                                 "Error reading file. Maybe your file is corrupt?\n" + str(e))
            return self.request, 'certificates/add.html', {"form": self.form}

    def _handle_x509(self):
        x509 = self.form.to_publickey()
        if x509.already_exists():
            messages.add_message(self.request, messages.WARNING,
                                 'Certificate ' + x509.subject.cname + ' has already existed!')
        else:
            x509.save_new()
        return self.request, 'certificates/added.html', {"public": x509}

    def _handle_privatekey(self):
        private = self.form.to_privatekey()
        if not private.certificate_exists():
            messages.add_message(self.request, messages.Error, 'No certificate exists for this private key. '
                                                               'Upload certificate first!')
            return self.request, 'certificates/add.html'

        if private.already_exists():
            messages.add_message(self.request, messages.WARNING, 'Private key has already existed!')
        else:
            private.save()
            private.connect_to_certificates()
        public = private.certificates.all()[0]
        return self.request, 'certificates/added.html', {"private": private, "public": public}

    def _handle_pkcs12(self):
        private = self.form.to_privatekey()
        public = self.form.to_publickey()
        further_publics = self.form.further_publics()

        if public.already_exists():
            messages.add_message(self.request, messages.WARNING,
                                 'Certificate ' + public.subject.cname + ' has already existed!')
        else:
            public.save_new()

        if private.already_exists():
            messages.add_message(self.request, messages.WARNING, 'Private key has already existed!')
        else:
            private.save()
            private.connect_to_certificates()

        for cert in further_publics:
            if cert.already_exists():
                messages.add_message(self.request, messages.WARNING,
                                     'Certificate ' + cert.subject.cname + ' has already existed!')
            else:
                cert.save_new()

        return self.request, 'certificates/added.html', {"private": private, "public": public,
                                                         "further_publics": further_publics}
