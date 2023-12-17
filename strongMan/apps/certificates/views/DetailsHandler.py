from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from ..models import UserCertificate, ViciCertificate, CertificateDoNotDelete
from ..forms import ChangeNicknameForm

import oscrypto.asymmetric

class DetailsHandler(object):
    def __init__(self, request, certificate_object):
        self.request = request
        self.certificate = certificate_object
        self._usercert = self._certificate_subclass(classe=UserCertificate)
        self._vicicert = self._certificate_subclass(classe=ViciCertificate)

    def _render_vici_details(self):
        return render(self.request, 'certificates/details.html',
                      {"certificate": self._vicicert, "readonly": True})

    def _render_user_details(self):
        if self._usercert.private_key is None:
            return render(self.request, 'certificates/details.html',
                          {"certificate": self._usercert, "readonly": False})
        else:
            return render(self.request, 'certificates/details.html',
                          {"certificate": self._usercert, 'private': self._usercert.private_key,
                           "readonly": False})

    def handle(self):
        if self._is_vicicert():
            return self._render_vici_details()

        if self.request.method == "GET":
            return self._render_user_details()
        elif self.request.method == "POST":
            if "export_cert" in self.request.POST:
                return self._export_certificate()
            if "remove_cert" in self.request.POST:
                return self._delete_cert()
            elif "remove_privatekey" in self.request.POST:
                return self._delete_private_key()
            elif "update_nickname" in self.request.POST:
                if not self._is_usercert():
                    return self._render_user_details()
                form = ChangeNicknameForm(self.request.POST)
                if form.is_valid():
                    self._usercert.nickname = form.cleaned_data["nickname"]
                    self._usercert.save()
                    return self._render_user_details()
        return self._render_user_details()

    def _certificate_subclass(self, classe):
        try:
            return classe.objects.get(id=self.certificate.id)
        except Exception:
            return None

    def _is_vicicert(self):
        return self._vicicert is not None

    def _is_usercert(self):
        return self._usercert is not None

    def _delete_cert(self):
        cname = self.certificate.subject.cname
        try:
            self.certificate.delete()
            messages.add_message(self.request, messages.INFO, "Certificate '" + cname + "' has been "
                                 "removed.")
            return HttpResponseRedirect(reverse('certificates:overview'))
        except CertificateDoNotDelete as e:
            messages.add_message(self.request, messages.ERROR, "Can't delete certificate. " + str(e))
            return self._render_user_details()

    def _delete_private_key(self):
        try:
            self._usercert.remove_privatekey()
            messages.add_message(self.request, messages.INFO, "Private key has been removed.")
        except CertificateDoNotDelete as e:
            messages.add_message(self.request, messages.ERROR, "Can't delete private key. " + str(e))

        return self._render_user_details()

    def _export_certificate(self):

        try:

            filename = self._usercert.nickname + '.pem'

            # Load DER-encoded certificate
            cert = oscrypto.asymmetric.load_certificate(self.certificate.der_container)

            # Export the certificate to PEM format
            pem_bytes = oscrypto.asymmetric.dump_certificate(cert)

            # Create an HttpResponse with the PEM formatted certificate
            response = HttpResponse(pem_bytes, content_type="application/x-pem-file")

            # Set the Content-Disposition header for the browser to prompt the user to download the file
            response['Content-Disposition'] = "attachment; filename=%s" % filename

            return response

        except Exception as e:
            messages.add_message(self.request, messages.ERROR, "Couldn't export the cert. " + str(e))
            return self._render_user_details()
