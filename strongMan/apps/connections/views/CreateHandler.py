from django.shortcuts import render, redirect
from django.urls import reverse

from ..forms.ConnectionForms import AbstractDynamicForm, ChooseTypeForm
from ..forms.SubForms import HeaderForm


class AddHandler(object):
    def __init__(self, request):
        self.request = request

    def _render(self, form=ChooseTypeForm()):
        return render(self.request, 'connections/Detail.html', {"form": form})

    def _abstract_form(self):
        '''
        Intiates and validates the Abstract form
        :return Valid abstract form
        '''
        form = AbstractDynamicForm(self.request.POST)
        if not form.is_valid():
            raise Exception("No valid form detected." + str(form.errors))
        return form

    def handle(self):
        if self.request.method == "GET":
            return self._render()
        elif self.request.method == "POST":
            abstract_form = self._abstract_form()
            form_class = abstract_form.current_form_class

            form = form_class(self.request.POST)
            form.update_certs()
            if not form.is_valid():
                return self._render(form)

            if form_class == ChooseTypeForm:
                return self._render(form=form.selected_form_class())

            if isinstance(form, HeaderForm):
                form.create_connection()
                return redirect(reverse("connections:index"))
