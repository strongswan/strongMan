import strongMan.apps.connections.forms.add_wizard
from ..models import Connection
from .. import forms
from django.shortcuts import render, redirect

class UpdateHandler:
    def __init__(self, request, id):
        self.request = request
        self.id = id

    def _render_get(self):
        connection = Connection.objects.get(id=self.id).subclass()
        form = forms.add_wizard.ConnectionForm().subclass(connection)
        form.fill(connection)
        return render(self.request, 'connections/connection_configuration.html',
                      {'form': form, 'form_name': self._get_type_name(form), 'title': self._get_title(form)})
    def handle(self):
        if self.request.method == 'GET':
            return self._render_get()

        #POST
        if self.request.POST["wizard_step"] == "update_certificate":
            form_name = self.request.POST['form_name']
            form_class = getattr(forms, form_name)
            form = form_class(initial=self.request.POST)
            form.update_certificates()
            return render(self.request, 'connections/connection_configuration.html',
                      {'form': form, 'form_name': self._get_type_name(form), 'title': self._get_title(form)})
        else:
            form_name = self.request.POST['form_name']
            form_class = getattr(forms, form_name)
            form = form_class(self.request.POST)
            form.update_certificates()
            if form.is_valid():
                form.update_connection(self.id)
                return redirect('/')
            else:
                return render(self.request, 'connections/connection_configuration.html',
                              {'form': form, 'form_name': self._get_type_name(form), 'title': self._get_title(form)})

    def _get_title(self, form):
        return form.get_choice_name()

    def _get_type_name(self, cls):
        return type(cls).__name__
