from django.shortcuts import render
from ..forms.add_wizard import Ike2CertificateForm
from ...certificates.models import UserCertificate
from django.shortcuts import get_object_or_404


class CaPickerHandler:
    def __init__(self, request):
        self.request = request

    def handle(self):
        form = Ike2CertificateForm()
        return render(self.request,
                      'connections/forms/CaPicker.html', {"certificate": form['certificate_ca']})

