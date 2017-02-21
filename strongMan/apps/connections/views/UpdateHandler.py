from django.shortcuts import render
from django.contrib import messages

from ..forms.ConnectionForms import AbstractConnectionForm, AbstractDynamicForm
from ..models.connections import Connection


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
        return render(self.request, 'connections/Detail.html', {"form": form, "connection": self.connection})

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
            abstract_form = self._abstract_form()
            form_class = abstract_form.current_form_class

            form = form_class(self.parameter_dict)
            form.update_certs()
            if not form.is_valid():
                return self._render(form)

            form.update_connection(self.id)
            messages.success(self.request, "Connection has been updated.")
            return self._render(form)
