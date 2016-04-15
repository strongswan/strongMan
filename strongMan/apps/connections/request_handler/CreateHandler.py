from django.shortcuts import render, redirect

import strongMan.apps.connections.forms.add_wizard
from .. import forms


class CreateHandler:
    def __init__(self, request):
        self.request = request

    def _render_select_type(self):
        return render(self.request, 'connections/select_typ.html', {'form': strongMan.apps.connections.forms.add_wizard.ChooseTypeForm()})

    def _render_configure(self, form, form_name):
        return render(self.request, 'connections/connection_configuration.html',
                      {'form': form, 'form_name': form_name, 'title': self._get_title(form)})

    def _init_form(self, data=None, initial=None):
        form_name = self.request.POST['form_name']
        form_class = getattr(forms, form_name)
        form = form_class(data=data, initial=initial)
        form.update_certificates()
        return form, form_name

    def _handle_select_type(self):
        form, form_name = self._init_form()
        return self._render_configure(form, form_name)

    def _handle_update_certificate(self):
        form, form_name = self._init_form(initial=self.request.POST)
        return self._render_configure(form, form_name)

    def _handle_configure(self):
        form, form_name = self._init_form(self.request.POST)
        if form.is_valid():
            form.create_connection()
            return redirect('/')
        else:
            return self._render_configure(form, form_name)

    def handle(self):
        if self.request.method == "GET":
            return self._render_select_type()

        # POST
        step = self.request.POST["wizard_step"]
        if step == "select_type":
            return self._handle_select_type()
        elif step == "update_certificate":
            return self._handle_update_certificate()
        elif step == "configure":
            return self._handle_configure()
        else:
            return self._render_select_type()

    def _get_title(self, form):
        return form.get_choice_name()

    def _get_type_name(self, cls):
        return type(cls).__name__
