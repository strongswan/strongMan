from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from .request_handler import AboutHandler, PwChangeHandler


@login_required
@require_http_methods(['GET', 'POST'])
def index(request):
    return render(request, 'index.html')


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
@require_http_methods(['GET', 'POST'])
def about(request):
    handler = AboutHandler(request)
    return handler.handle()


@login_required
@require_http_methods(['GET', 'POST'])
def pw_change(request):
    handler = PwChangeHandler(request)
    return handler.handle()


def bad_request(request, exception=None):
    return render(request, '400.html', status=400)


def permission_denied(request, exception=None):
    return render(request, '403.html', status=403)


def page_not_found(request, exception=None):
    return render(request, '404.html', status=404)


def server_error(request):
    return render(request, '500.html', status=500)
