from django.shortcuts import render, get_object_or_404

from ..forms.ConnectionForms import Ike2CertificateForm
from ...certificates.models import UserCertificate


class CertificatePickerHandler(object):
    def __init__(self, request):
        self.request = request

    def _render(self, form):
        return render(self.request,
                      'server_connections/forms/CertificatePicker.html',
                      {"certificate": form['certificate'], "identity": form['identity']})

    def handle(self):
        cert = self._certificate_id()

        if cert is None:
            form = Ike2CertificateForm()
        else:
            form = Ike2CertificateForm(initial={'certificate': cert})

        form.update_certificates()
        return self._render(form)

    def _certificate_id(self):
        if "certififcate_id" not in self.request.POST:
            return None

        cert = self.request.POST["certififcate_id"]
        if cert == "-1" or cert == '':
            return None

        get_object_or_404(UserCertificate, pk=cert)
        return cert
