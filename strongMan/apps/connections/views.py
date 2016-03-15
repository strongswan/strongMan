import socket
from collections import OrderedDict
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import FormView
from .forms import Ike2CertificateForm, Ike2EapForm, ChooseTypeForm
from .models import Connection, Address, Secret
from strongMan.apps.vici import vici


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
        remote_addresses = Address.objects.filter(remote_addresses=connection)
        initial["profile"] = connection.profile
        initial["gateway"] = remote_addresses[0].value
        return initial


class Ike2EapCreateView(LoginRequiredMixin, FormView):
    template_name = 'connection_form.html'
    form_class = Ike2EapForm
    success_url = reverse_lazy("index")

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
        remote_addresses = Address.objects.filter(remote_addresses=connection)
        secrets = Secret.objects.filter(connection=connection)
        initial["profile"] = connection.profile
        initial["gateway"] = remote_addresses[0].value
        initial["password"] = secrets[0].data
        return initial


@login_required
@require_http_methods('POST')
def toggle_connection(request):
    connection = Connection.objects.get(id=request.POST['id'])
    connection.state = not connection.state
    connection.save()
    so = socket.socket(socket.AF_UNIX)
    so.connect("/var/run/charon.vici")
    s = vici.Session(so)
    if connection.state is True:
        s.load_conn(connection.get_vici_ordered_dict())
        for secret in Secret.objects.filter(connection=connection):
            s.load_shared(secret.get_vici_ordered_dict())
    else:
        s.unload_conn(OrderedDict(name=connection.profile))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
