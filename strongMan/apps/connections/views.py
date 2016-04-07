from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import FormView
from .models import Connection, Secret, Address
from . import models
from . import forms
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper
from strongMan.apps.vici.wrapper.exception import ViciSocketException, ViciLoadException


@require_http_methods('GET')
@login_required
def overview(request):
    try:
        vici_wrapper = ViciWrapper()
        for connection in Connection.objects.all():
            connection.state = vici_wrapper.is_connection_active(connection.profile)
            connection.save()
    except ViciSocketException as e:
        messages.warning(request, str(e))
    except ViciLoadException as e:
        messages.warning(request, str(e))

    connections = []

    for cls in Connection.get_types():
        connection_class = getattr(models, cls)
        for connection in connection_class.objects.all():
            connection_dict = dict(id=connection.id, profile=connection.profile, state=connection.state)
            address = Address.objects.filter(remote_addresses=connection).first()
            connection_dict['remote'] = address.value
            connection_dict['edit'] = "/connections/" + str(connection.id)
            connection_dict['connection_type'] = cls
            connection_dict['delete'] = "/connections/delete/" + str(connection.id)
            connections.append(connection_dict)

    context = dict(connections=connections)
    return render(request, 'index.html', context)


class ChooseTypView(LoginRequiredMixin, FormView):
    template_name = 'connections/select_typ.html'
    form_class = forms.ChooseTypeForm

    def form_valid(self, form):
        form_name = self.request.POST['typ']
        form_class = getattr(forms, form_name)
        form = form_class()
        return render(self.request, 'connections/connection_configuration.html',
                      {'form': form_class(), 'form_name': form_name, 'title': _get_title(form)})


@login_required
def create(request):
    if request.method == 'GET':
        form_name = request.POST['typ']
        form_class = getattr(forms, form_name)
        form = form_class()
        return render(request, 'connections/connection_configuration.html',
                      {'form': form_class(), 'form_name': form_name, 'title': _get_title(form)})

    elif request.method == 'POST':
        form_name = request.POST['form_name']
        form_class = getattr(forms, form_name)
        form = form_class(request.POST)
        if form.is_valid():
            form.create_connection()
            return redirect('/')
        else:
            return render(request, 'connections/connection_configuration.html', {'form': form, 'title': _get_title(form)})


@login_required
def update(request, id):
    if request.method == 'GET':
        connection = Connection.objects.get(id=id).subclass()
        form = forms.ConnectionForm().subclass(connection)
        form.fill(connection)
        return render(request, 'connections/connection_configuration.html',
                      {'form': form, 'form_name': _get_type_name(form), 'title': _get_title(form)})
    elif request.method == 'POST':
        form_name = request.POST['form_name']
        form_class = getattr(forms, form_name)
        form = form_class(request.POST)
        if form.is_valid():
            form.update_connection(id)
            return redirect('/')
        else:
            return render(request, 'connections/connection_configuration.html',
                          {'form': form, 'form_name': _get_type_name(form), 'title': _get_title(form)})


@login_required
@require_http_methods('POST')
def toggle_connection(request):
    connection = Connection.objects.get(id=request.POST['id']).subclass()
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
def delete_connection(request, id):
    connection = Connection.objects.get(id=id).subclass()
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


def _get_title(form):
    return form.get_choice_name()


def _get_type_name(cls):
    return type(cls).__name__

