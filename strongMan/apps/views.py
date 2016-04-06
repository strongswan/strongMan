from collections import OrderedDict
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .connections.models import Connection, Address
from .connections import models
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


@require_http_methods(('GET', 'POST'))
def login(request):
    if request.method == 'POST':
        password = request.POST.get('password', None)
        username = request.POST.get('username', None)
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return redirect('/')
            else:
                messages.error(request, "The password is valid, but the account has been disabled!")
        else:
            messages.error(request, "The username and password were incorrect.")
            return redirect('/')
    return render(request, 'login.html')


@require_http_methods('GET')
def logout(request):
    auth_logout(request)
    return render(request, 'login.html')


@login_required
@require_http_methods('GET')
def about(request):
    context = OrderedDict()
    try:
        vici_wrapper = ViciWrapper()
        context = vici_wrapper.get_version()
        context['plugins'] = vici_wrapper.get_plugins()
    except ViciSocketException as e:
        messages.warning(request, str(e))
    except ViciLoadException as e:
        messages.warning(request, str(e))

    return render(request, 'about.html', context)
