from django.shortcuts import render
from ..forms import Ike2CertificateForm
from ...certificates.models import UserCertificate
from django.shortcuts import get_object_or_404


class CertificatePickerHandler:
    def __init__(self, request):
        self.request = request

    def _render(self, form):
        return render(self.request,
                      'connections/forms/CertificatePicker.html',
                      {"certificate": form['certificate'], "identity": form['identity']})

    def handle(self):
        id = self._certificate_id()

        if id is None:
            form = Ike2CertificateForm()
        else:
            form = Ike2CertificateForm(initial={'certificate': id})

        form.update_certificates()
        return self._render(form)

    def _certificate_id(self):
        if "certififcate_id" not in self.request.POST:
            return None

        id = self.request.POST["certififcate_id"]
        if id == "-1" or id == '':
            return None

        get_object_or_404(UserCertificate, pk=id)
        return id
