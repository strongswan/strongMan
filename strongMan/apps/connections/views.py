from collections import OrderedDict
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import FormView
from .forms import Ike2CertificateForm, Ike2EapForm, ChooseTypeForm, Ike2EapCertificateForm
from .models import Connection, Address, Secret, Typ
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper


class ChooseTypView(LoginRequiredMixin, FormView):
    template_name = 'select_form.html'
    form_class = ChooseTypeForm

    def form_valid(self, form):
        self.success_url = "/connection/create/" + self.request.POST['typ']
        return super(ChooseTypView, self).form_valid(form)


class Ike2CertificateCreateView(LoginRequiredMixin, FormView):
    template_name = 'connection_form.html'
    form_class = Ike2CertificateForm
    success_url = reverse_lazy("index")

    def get_context_data(self, **kwargs):
        context = super(Ike2CertificateCreateView, self).get_context_data(**kwargs)
        context['title'] = Typ.objects.get(id=1).name
        return context

    def form_valid(self, form):
        form.create_connection()
        return super(Ike2CertificateCreateView, self).form_valid(form)


class Ike2CertificateUpdateView(LoginRequiredMixin, FormView):
    template_name = 'connection_form.html'
    form_class = Ike2CertificateForm
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        form.update_connection(self.kwargs['pk'])
        return super(Ike2CertificateUpdateView, self).form_valid(form)

    def get_initial(self):
        initial = super(Ike2CertificateUpdateView, self).get_initial()
        connection = Connection.objects.get(id=self.kwargs['pk'])
        remote_address = Address.objects.filter(remote_addresses=connection).first()
        initial["profile"] = connection.profile
        initial["gateway"] = remote_address.value
        return initial

    def get_context_data(self, **kwargs):
        context = super(Ike2CertificateUpdateView, self).get_context_data(**kwargs)
        context['title'] = Typ.objects.get(id=1).name
        return context


class Ike2EapCreateView(LoginRequiredMixin, FormView):
    template_name = 'connection_form.html'
    form_class = Ike2EapForm
    success_url = reverse_lazy("index")

    def get_context_data(self, **kwargs):
        context = super(Ike2EapCreateView, self).get_context_data(**kwargs)
        context['title'] = Typ.objects.get(id=2).name
        return context

    def form_valid(self, form):
        form.create_connection()
        return super(Ike2EapCreateView, self).form_valid(form)


class Ike2EapUpdateView(LoginRequiredMixin, FormView):
    template_name = 'connection_form.html'
    form_class = Ike2EapForm
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        form.update_connection(self.kwargs['pk'])
        return super(Ike2EapUpdateView, self).form_valid(form)

    def get_initial(self):
        initial = super(Ike2EapUpdateView, self).get_initial()
        connection = Connection.objects.get(id=self.kwargs['pk'])
        remote_address = Address.objects.filter(remote_addresses=connection).first()
        secret = Secret.objects.filter(connection=connection).first()
        initial["profile"] = connection.profile
        initial["gateway"] = remote_address.value
        initial["password"] = secret.data
        return initial

    def get_context_data(self, **kwargs):
            context = super(Ike2EapUpdateView, self).get_context_data(**kwargs)
            context['title'] = Typ.objects.get(id=2).name
            return context


class Ike2EapCertificateCreateView(LoginRequiredMixin, FormView):
    template_name = 'connection_form.html'
    form_class = Ike2EapCertificateForm
    success_url = reverse_lazy("index")

    def get_context_data(self, **kwargs):
        context = super(Ike2EapCertificateCreateView, self).get_context_data(**kwargs)
        context['title'] = Typ.objects.get(id=3).name
        return context

    def form_valid(self, form):
        form.create_connection()
        return super(Ike2EapCertificateCreateView, self).form_valid(form)


class Ike2EapCertificateUpdateView(LoginRequiredMixin, FormView):
    template_name = 'connection_form.html'
    form_class = Ike2EapCertificateForm
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        form.update_connection(self.kwargs['pk'])
        return super(Ike2EapCertificateUpdateView, self).form_valid(form)

    def get_initial(self):
        initial = super(Ike2EapCertificateUpdateView, self).get_initial()
        connection = Connection.objects.get(id=self.kwargs['pk'])
        remote_address = Address.objects.filter(remote_addresses=connection).first()
        secret = Secret.objects.filter(connection=connection).first()
        initial["profile"] = connection.profile
        initial["gateway"] = remote_address.value
        initial["password"] = secret.data
        return initial

    def get_context_data(self, **kwargs):
        context = super(Ike2EapCertificateUpdateView, self).get_context_data(**kwargs)
        context['title'] = Typ.objects.get(id=3).name
        return context


@login_required
@require_http_methods('POST')
def toggle_connection(request):
    connection = Connection.objects.get(id=request.POST['id'])
    connection.state = not connection.state
    connection.save()
    vici_wrapper = ViciWrapper()
    if connection.state is True:
        vici_wrapper.load_connection(connection.get_vici_ordered_dict())
        for secret in Secret.objects.filter(connection=connection):
            vici_wrapper.load_secret(secret.get_vici_ordered_dict())
    else:
        vici_wrapper.unload_connection(OrderedDict(name=connection.profile))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
