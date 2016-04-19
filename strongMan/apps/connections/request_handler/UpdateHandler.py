
from ..models import Connection
from .. import forms
from django.shortcuts import render, redirect


class UpdateHandler:
    def __init__(self, request, id):
        self.request = request
        self.id = id


    @property
    def connection(self):
        return Connection.objects.get(pk=self.id).subclass()

    def _render_get(self):
        form = forms.add_wizard.ConnectionForm().subclass(self.connection)
        form.fill(self.connection)
        return render(self.request, 'connections/connection_configuration.html',
                      {'form': form, 'form_name': self._get_type_name(form), 'title': self._get_title(form),'connection': self.connection})

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
                      {'form': form, 'form_name': self._get_type_name(form), 'title': self._get_title(form),'connection': self.connection})
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
                              {'form': form, 'form_name': self._get_type_name(form), 'title': self._get_title(form),'connection': self.connection})

    def _get_title(self, form):
        return form.get_choice_name


    def _get_type_name(self, cls):
        return type(cls).__name__

