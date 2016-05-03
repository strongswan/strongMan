from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse

from .. import forms

class AddHandler:
    def __init__(self, request):
        self.request = request

    def _render(self, form=forms.ChooseTypeForm()):
        return render(self.request, 'connections/Detail.html', {"form": form})

    def _abstract_form(self):
        '''
        Intiates and validates the Abstract form
        :return Valid abstract form
        '''
        form = forms.AbstractConForm(self.request.POST)
        if not form.is_valid():
            raise Exception("No valid form detected." + str(form.errors))
        return form

    def handle(self):
        if self.request.method == "GET":
            return self._render()
        elif self.request.method == "POST":
            abstract_form = self._abstract_form()
            form_class = abstract_form.current_form_class

            if abstract_form.refresh_choices_requested:
                form = form_class(initial=self.request.POST)
                form.update_certificates()
                return self._render(form)

            form = form_class(self.request.POST)
            form.update_certificates()
            if not form.is_valid():
                return self._render(form)

            if form_class == forms.ChooseTypeForm:
                return self._render(form=form.selected_form_class())

            if isinstance(form, forms.ConnectionForm):
                form.create_connection()
                return redirect(reverse("connections:index"))

