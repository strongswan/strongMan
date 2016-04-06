from django.contrib import messages
from oscrypto.errors import AsymmetricKeyError

from strongMan.apps.certificates.forms import AddForm
from ..services import UserCertificateManager


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