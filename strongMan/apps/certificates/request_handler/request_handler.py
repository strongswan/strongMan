from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render, HttpResponseRedirect
from oscrypto.errors import AsymmetricKeyError

from strongMan.apps.certificates.container_reader import ContainerTypes
from strongMan.apps.certificates.forms import AddForm
from ..services import UserCertificateManager, CertificateManagerException
from ..models import UserCertificate, ViciCertificate


class DetailsHandler:
    def __init__(self, request, certificate_object):
        self.request = request
        self.certificate = certificate_object
        self._usercert = self._certificate_subclass(classe=UserCertificate)
        self._vicicert = self._certificate_subclass(classe=ViciCertificate)

    def _render_vici_details(self):
        return render(self.request, 'certificates/details.html', {"certificate": self._vicicert, "readonly": True})

    def _render_user_details(self):
        if self._usercert.private_key is None:
            return render(self.request, 'certificates/details.html', {"certificate": self._usercert, "readonly": False})
        else:
            return render(self.request, 'certificates/details.html',
                          {"certificate": self._usercert, 'private': self._usercert.private_key, "readonly": False})

    def handle(self):
        if self._is_vicicert():
            return self._render_vici_details()

        if self.request.method == "GET":
            return self._render_user_details()
        elif self.request.method == "POST":
            if "remove_cert" in self.request.POST:
                cname = self.certificate.subject.cname
                self.certificate.delete()
                messages.add_message(self.request, messages.INFO, "Certificate " + cname + " has been removed.")
                return HttpResponseRedirect(reverse('certificates:overview'))
            elif "remove_privatekey" in self.request.POST:
                self._usercert.remove_privatekey()
                messages.add_message(self.request, messages.INFO, "Private key has been removed.")
                return self._render_user_details()
        return self._render_user_details()

    def _certificate_subclass(self, classe):
        try:
            return classe.objects.get(id=self.certificate.id)
        except Exception as e:
            return None

    def _is_vicicert(self):
        return not self._vicicert == None

    def _is_usercert(self):
        return not self._usercert == None




class AddHandler:
    def __init__(self):
        self.form = None
        self.request = None

    @classmethod
    def by_request(cls, request):
        handler = cls()
        handler.request = request
        return handler

    def _render_upload_page(self):
        return self.request, 'certificates/add.html', {"form": AddForm()}

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
            type = self.form.container_type()
            if type == ContainerTypes.X509:
                return self._handle_x509()
            elif type == ContainerTypes.PKCS1 or type == ContainerTypes.PKCS8:
                return self._handle_privatekey()
            elif type == ContainerTypes.PKCS12:
                return self._handle_pkcs12()
        except (ValueError, TypeError, AsymmetricKeyError, OSError) as e:
            messages.add_message(self.request, messages.ERROR,
                                 "Error reading file. Maybe your file is corrupt?")
            return self.request, 'certificates/add.html', {"form": self.form}
        except Exception as e:
            messages.add_message(self.request, messages.ERROR,
                                 "Internal error: " + str(e))
            return self.request, 'certificates/add.html', {"form": self.form}

    def _handle_x509(self):
        x509reader = self.form.container_reader()
        try:
            cert = UserCertificateManager.add_x509(x509reader)
            if cert.private_key == None:
                return self.request, 'certificates/added.html', {"public": cert}
            else:
                return self.request, 'certificates/added.html', {"private": cert.private_key, "public": cert}
        except CertificateManagerException as e:
            messages.add_message(self.request, messages.ERROR, str(e))
            return self._render_upload_page()

    def _handle_privatekey(self):
        privatekey_reader = self.form.container_reader()
        try:
            privatekey = UserCertificateManager.add_pkcs1_or_8(privatekey_reader)
            public = privatekey.certificates.all()[0]
            return self.request, 'certificates/added.html', {"private": privatekey, "public": public}
        except CertificateManagerException as e:
            messages.add_message(self.request, messages.ERROR, str(e))
            return self._render_upload_page()

    def _handle_pkcs12(self):
        pkcs12reader = self.form.container_reader()
        cert = None
        privatekey = None
        further_certs = []

        x509reader = pkcs12reader.public_key()
        try:
            cert = UserCertificateManager.add_x509(x509reader)
        except CertificateManagerException as e:
            messages.add_message(self.request, messages.ERROR, str(e))

        private_reader = pkcs12reader.private_key()
        try:
            privatekey = UserCertificateManager.add_pkcs1_or_8(private_reader)
        except CertificateManagerException as e:
            messages.add_message(self.request, messages.ERROR, str(e))

        further_x509reader = pkcs12reader.further_publics()
        for x509read in further_x509reader:
            try:
                further = UserCertificateManager.add_x509(x509read)
                further_certs.append(further)
            except CertificateManagerException as e:
                messages.add_message(self.request, messages.ERROR, str(e))

        nothing_added = cert == None and privatekey == None and len(further_certs) == 0
        if nothing_added:
            return self._render_upload_page()

        return self.request, 'certificates/added.html', {"private": privatekey, "public": cert,
                                                         "further_publics": further_certs}
