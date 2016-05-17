from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, render_to_response
from django.views.decorators.http import require_http_methods
from django.template import RequestContext

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


def bad_request(request):
    response = render_to_response('400.html', context_instance=RequestContext(request))
    response.status_code = 400
    return response


def permission_denied(request):
    response = render_to_response('403.html', context_instance=RequestContext(request))
    response.status_code = 403
    return response


def page_not_found(request):
    response = render_to_response('404.html', context_instance=RequestContext(request))
    response.status_code = 404
    return response


def server_error(request):
    response = render_to_response('500.html', context_instance=RequestContext(request))
    response.status_code = 500
    return response
