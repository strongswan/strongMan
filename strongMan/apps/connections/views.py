from django.views.generic.edit import CreateView, UpdateView
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Connection, Address
from . import forms


class ConnectionCreateView(LoginRequiredMixin, CreateView):
    model = Connection
    #fields = ['profile', 'local_addresses', 'remote_addresses', 'version', 'auth', 'vips']
    form_class = forms.ConnectionAddressFormSet
    success_url = reverse_lazy("index")


class ConnectionUpdateView(LoginRequiredMixin, UpdateView):
    model = Connection
    fields = ['profile', 'local_addresses', 'remote_addresses', 'version', 'auth', 'vips']
    success_url = reverse_lazy("index")


