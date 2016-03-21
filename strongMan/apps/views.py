from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .connections.models import Connection, Address
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper


@require_http_methods('GET')
@login_required
def overview(request):
    vici_wrapper = ViciWrapper()
    active_connections = vici_wrapper.get_connections_names()
    print(active_connections)
    connections = []
    for conn in Connection.objects.all():
        connection = dict(id=conn.id, profile=conn.profile, state=conn.state)
        address = Address.objects.filter(remote_addresses=conn).first()
        connection['remote'] = address.value
        connection['link'] = "/connection/update/"+str(conn.typ.id)+"/"+str(conn.id)
        connections.append(connection)
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


@require_http_methods('GET')
def about(request):
    return render(request, 'about.html')