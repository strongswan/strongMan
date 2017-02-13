import sys

from django import forms
from strongMan.apps.connections.forms.SubForms import HeaderForm, CaCertificateForm, \
    ServerIdentityForm, UserCertificateForm, EapForm, EapTlsForm
from strongMan.apps.connections.models.connections import IKEv2Certificate, IKEv2EAP, IKEv2CertificateEAP, \
    IKEv2EapTls


class AbstractDynamicForm(forms.Form):
    refresh_choices = forms.CharField(max_length=10, required=False)
    current_form = forms.CharField(max_length=100, required=True)

    @property
    def current_form_class(self):
        current_form_name = self.cleaned_data["current_form"]
        return getattr(sys.modules[__name__], current_form_name)

    @property
    def template(self):
        raise NotImplementedError

    def update_certs(self):
        pass


class ChooseTypeForm(AbstractDynamicForm):
    form_name = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(ChooseTypeForm, self).__init__(*args, **kwargs)
        self.fields['form_name'].choices = ChooseTypeForm.get_choices()

    @property
    def selected_form_class(self):
        name = self.cleaned_data["form_name"]
        return getattr(sys.modules[__name__], name)

    @property
    def template(self):
        return "connections/forms/ChooseType.html"

    @classmethod
    def get_choices(cls):
        return tuple(
                tuple((type(subclass()).__name__, subclass().model.choice_name)) for subclass in
                AbstractConnectionForm.__subclasses__())


class AbstractConnectionForm(AbstractDynamicForm):
    def is_valid(self):
        valid = True
        # Call is_valid method for every base class
        for base in self.__class__.__bases__:
            if base == AbstractConnectionForm:
                continue
            if hasattr(base, "is_valid"):
                valid = base.is_valid(self)
                if not valid:
                    valid = False
        return valid

    def create_connection(self):
        connection = self.model(profile=self.cleaned_data['profile'], auth='pubkey', version=2)
        connection.save()
        # Call create_connection method for every base class
        for base in self.__class__.__bases__:
            if base == AbstractConnectionForm:
                continue
            if hasattr(base, "create_connection"):
                base.create_connection(self, connection)
        return connection

    def update_connection(self, pk):
        connection = self.model.objects.get(id=pk)
        for base in self.__class__.__bases__:
            if base == AbstractConnectionForm:
                continue
            if hasattr(base, "update_connection"):
                base.update_connection(self, connection)
        return connection

    def fill(self, connection):
        # Call fill method for every base class
        for base in self.__class__.__bases__:
            if base == AbstractConnectionForm:
                continue
            if hasattr(base, "fill"):
                base.fill(self, connection)

    @classmethod
    def get_models(cls):
        return tuple(
                tuple((subclass().model(), type(subclass()).__name__)) for subclass in cls.__subclasses__())

    @classmethod
    def subclass(self, connection):
        typ = type(connection)
        for model, form_name in self.get_models():
            if type(model) == typ:
                form_class = getattr(sys.modules[__name__], form_name)
                return form_class()
        return self


class Ike2CertificateForm(AbstractConnectionForm, HeaderForm, UserCertificateForm, CaCertificateForm,
                          ServerIdentityForm):
    @property
    def model(self):
        return IKEv2Certificate

    @property
    def template(self):
        return "connections/forms/Ike2Certificate.html"

    def update_certs(self):
        self.update_certificates()


class Ike2EapForm(AbstractConnectionForm, HeaderForm, CaCertificateForm, ServerIdentityForm, EapForm):
    @property
    def model(self):
        return IKEv2EAP

    @property
    def template(self):
        return "connections/forms/Ike2EAP.html"


class Ike2EapCertificateForm(AbstractConnectionForm, HeaderForm, UserCertificateForm, CaCertificateForm,
                             ServerIdentityForm, EapForm):
    @property
    def model(self):
        return IKEv2CertificateEAP

    @property
    def template(self):
        return "connections/forms/Ike2EapCertificate.html"

    def update_certs(self):
        self.update_certificates()


class Ike2EapTlsForm(AbstractConnectionForm, HeaderForm, CaCertificateForm, ServerIdentityForm, EapTlsForm):
    @property
    def model(self):
        return IKEv2EapTls

    @property
    def template(self):
        return "connections/forms/Ike2EapTls.html"

    def update_certs(self):
        self.update_certificates()
