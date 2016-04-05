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
        return not self._vicicert is None

    def _is_usercert(self):
        return not self._usercert is None




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
            result = UserCertificateManager.add_keycontainer(self.form._cert_bytes(), self.form._read_password())
            for e in result.exceptions:
                messages.add_message(self.request, messages.WARNING, str(e))
            if not result.success:
                return self._render_upload_page()

            if result.certificate is not None and result.privatekey is None:
                result.privatekey = result.certificate.private_key
            if result.certificate is None and result.privatekey is not None:
                result.certificate = result.privatekey.certificates.all()[0]


            return self.request, 'certificates/added.html', {"private": result.privatekey, "public": result.certificate,
                                                             "further_publics": result.further_certificates}

        except (ValueError, TypeError, AsymmetricKeyError, OSError) as e:
            messages.add_message(self.request, messages.ERROR,
                                 "Error reading file. Maybe your file is corrupt?")
            return self.request, 'certificates/add.html', {"form": self.form}
        except Exception as e:
            messages.add_message(self.request, messages.ERROR,
                                 "Internal error: " + str(e))
            return self.request, 'certificates/add.html', {"form": self.form}