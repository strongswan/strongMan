from django.shortcuts import render, redirect
from .. import forms


class CreateHandler:
    def __init__(self, request):
        self.request = request

    def _render_select_type(self):
        return render(self.request, 'connections/select_typ.html', {'form': forms.ChooseTypeForm()})

    def _render_configure(self, form_class):
        form_name = self._get_type_name(form_class)
        form = form_class()
        return render(self.request, 'connections/connection_configuration.html',
                      {'form': form, 'form_name': form_name, 'title': self._get_title(form)})

    def handle(self):
        if self.request.method == "GET":
            return self._render_select_type()

        # POST
        step = self.request.POST["wizard_step"]
        if step == "select_type":
            form_name = self.request.POST['typ']
            form_class = getattr(forms, form_name)
            form = form_class()
            return render(self.request, 'connections/connection_configuration.html',
                          {'form': form_class(), 'form_name': form_name, 'title': self._get_title(form)})
        elif step == "configure":
            form_name = self.request.POST['form_name']
            form_class = getattr(forms, form_name)
            form = form_class(self.request.POST)
            if form.is_valid():
                form.create_connection()
                return redirect('/')
            else:
                return render(self.request, 'connections/connection_configuration.html',
                              {'form': form, 'form_name': form_name, 'title': self._get_title(form)})

    def _get_title(self, form):
        return form.get_choice_name()

    def _get_type_name(self, cls):
        return type(cls).__name__