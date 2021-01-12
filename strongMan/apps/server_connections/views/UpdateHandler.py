from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages

from ..forms.ConnectionForms import AbstractConnectionForm, AbstractDynamicForm
from ..models.connections import Connection
from .ToggleHandler import ToggleHandler


class UpdateHandler(object):
    def __init__(self, request, id):
        self.request = request
        self.id = id

    @property
    def connection(self):
        return Connection.objects.get(pk=self.id).subclass()

    @property
    def parameter_dict(self):
        parameters = self.request.POST.copy()
        parameters['connection_id'] = self.id
        return parameters

    def _render(self, form=None):
        if form is None:
            form = AbstractConnectionForm.subclass(self.connection)
            form.fill(self.connection)
        form.connection_type = self.connection.connection_type
        return render(self.request, 'server_connections/Detail.html',
                      {"form": form, "connection": self.connection})

    def _render_readonly(self, form=None):
        if form is None:
            form = AbstractConnectionForm.subclass(self.connection)
            form.fill(self.connection)
        return render(self.request, 'server_connections/widgets/readonly_table.html',
                      {"form": form, "connection": self.connection})

    def _abstract_form(self):
        '''
        Intiates and validates the Abstract form
        :return Valid abstract form
        '''
        form = AbstractDynamicForm(self.parameter_dict)
        if not form.is_valid():
            raise Exception("No valid form detected." + str(form.errors))
        return form

    def handle(self):
        if self.request.method == "GET":
            return self._render()
        elif self.request.method == "POST":
            if 'readonly' in self.request.POST:
                return self._render_readonly()
            elif 'save_and_reload' in self.request.POST:
                abstract_form = self._abstract_form()
                form_class = abstract_form.current_form_class

                form = form_class(self.parameter_dict)
                form.update_certs()
                if not form.is_valid():
                    return self._render(form)

                handler = ToggleHandler(self.request)
                handler.unload(self.id)
                form.update_connection(self.id)
                handler.load(self.id)
                messages.success(self.request, "Connection " + self.connection.profile +
                                 " has been updated and reloaded.")
                return redirect(reverse("server_connections:index"))
            else:
                abstract_form = self._abstract_form()
                form_class = abstract_form.current_form_class

                form = form_class(self.parameter_dict)
                form.update_certs()
                if not form.is_valid():
                    return self._render(form)

                form.update_connection(self.id)

                messages.success(self.request, "Connection " + self.connection.profile +
                                 " has been updated.")
                return redirect(reverse("server_connections:index"))
