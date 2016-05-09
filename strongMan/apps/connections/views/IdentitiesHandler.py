from django.shortcuts import render
from ..forms.add_wizard import Ike2CertificateForm
from ...certificates.models import UserCertificate
from django.shortcuts import get_object_or_404


class IdentitiesHandler:
    def __init__(self, request):
        self.request = request

    def _render(self, form):
        return render(self.request, 'connections/forms/IdentitiesPicker.html', {"identity": form['identity']})

    def handle(self):
        id = self._certificate_id()
        form = Ike2CertificateForm(initial={'certificate': id})
        form.update_certificates()
        return self._render(form)

    def _certificate_id(self):
        if "certififcate_id" not in self.request.POST:
            raise Exception("certififcate_id not found")

        id = self.request.POST["certififcate_id"]
        get_object_or_404(UserCertificate, pk=id)
        return id
