from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import FormView
from .forms import Ike2CertificateForm, Ike2EapForm, ChooseTypeForm, Ike2EapCertificateForm
from .models import Connection, Address, Secret, Typ
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper
from strongMan.apps.vici.wrapper.exception import ViciSocketException, ViciLoadException


class ChooseTypView(LoginRequiredMixin, FormView):
    template_name = 'connections/select_typ.html'
    form_class = ChooseTypeForm

    def form_valid(self, form):
        self.success_url = "/connection/create/" + self.request.POST['typ']
        return super(ChooseTypView, self).form_valid(form)


class Ike2CertificateCreateView(LoginRequiredMixin, FormView):
    template_name = 'connections/connection_configuration.html'
    form_class = Ike2CertificateForm
    success_url = reverse_lazy("index")

    def get_context_data(self, **kwargs):
        context = super(Ike2CertificateCreateView, self).get_context_data(**kwargs)
        context['title'] = Typ.objects.get(id=1).value
        return context

    def form_valid(self, form):
        form.create_connection()
        return super(Ike2CertificateCreateView, self).form_valid(form)


class Ike2CertificateUpdateView(LoginRequiredMixin, FormView):
    template_name = 'connections/connection_configuration.html'
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
        initial["certificate"] = connection.domain
        return initial

    def get_context_data(self, **kwargs):
        context = super(Ike2CertificateUpdateView, self).get_context_data(**kwargs)
        context['title'] = Typ.objects.get(id=1).value
        return context


class Ike2EapCreateView(LoginRequiredMixin, FormView):
    template_name = 'connections/connection_configuration.html'
    form_class = Ike2EapForm
    success_url = reverse_lazy("index")

    def get_context_data(self, **kwargs):
        context = super(Ike2EapCreateView, self).get_context_data(**kwargs)
        context['title'] = Typ.objects.get(id=2).value
        return context

    def form_valid(self, form):
        form.create_connection()
        return super(Ike2EapCreateView, self).form_valid(form)


class Ike2EapUpdateView(LoginRequiredMixin, FormView):
    template_name = 'connections/connection_configuration.html'
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
            context['title'] = Typ.objects.get(id=2).value
            return context


class Ike2EapCertificateCreateView(LoginRequiredMixin, FormView):
    template_name = 'connections/connection_configuration.html'
    form_class = Ike2EapCertificateForm
    success_url = reverse_lazy("index")

    def get_context_data(self, **kwargs):
        context = super(Ike2EapCertificateCreateView, self).get_context_data(**kwargs)
        context['title'] = Typ.objects.get(id=3).value
        return context

    def form_valid(self, form):
        form.create_connection()
        return super(Ike2EapCertificateCreateView, self).form_valid(form)


class Ike2EapCertificateUpdateView(LoginRequiredMixin, FormView):
    template_name = 'connections/connection_configuration.html'
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
        initial["certificate"] = connection.domain
        return initial

    def get_context_data(self, **kwargs):
        context = super(Ike2EapCertificateUpdateView, self).get_context_data(**kwargs)
        context['title'] = Typ.objects.get(id=3).value
        return context


@login_required
@require_http_methods('POST')
def toggle_connection(request):
    connection = Connection.objects.get(id=request.POST['id'])
    response = dict(id=request.POST['id'], success=False)
    try:
        vici_wrapper = ViciWrapper()
        if vici_wrapper.is_connection_active(connection.profile) is False:
            vici_wrapper.load_connection(connection.dict())
            for secret in Secret.objects.filter(connection=connection):
                vici_wrapper.load_secret(secret.dict())
                connection.state = True
        else:
            vici_wrapper.unload_connection(connection.profile)
            connection.state = False
        connection.save()
        response['success'] = True
    except ViciSocketException as e:
        response['message'] = str(e)
    except ViciLoadException as e:
        response['message'] = str(e)
    finally:
        return JsonResponse(response)


@login_required
def delete_connection(request, pk):
    connection = Connection.objects.get(id=pk)
    try:
        vici_wrapper = ViciWrapper()
        if vici_wrapper.is_connection_active(connection.profile) is True:
            vici_wrapper.unload_connection(connection.profile)
    except ViciSocketException as e:
        messages.warning(request, str(e))
    except ViciLoadException as e:
        messages.warning(request, str(e))
    finally:
        connection.delete_all_connected_models()
        connection.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
