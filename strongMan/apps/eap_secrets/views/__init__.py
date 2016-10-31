from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, get_object_or_404


from .OverviewHandler import OverviewHandler
from .AddHandler import AddHandler
from .EditHandler import EditHandler
from ..forms import AddOrEditForm
from ...server_connections.models import Secret


@login_required
@require_http_methods(["GET", "POST"])
def overview(request):
    handler = OverviewHandler.by_request(request)
    return handler.handle()


@login_required
@require_http_methods(["GET", "POST"])
def add(request):
    if request.method == 'POST':
        handler = AddHandler.by_request(request)
        return handler.handle()
    elif request.method == 'GET':
        return render(request, 'eap_secrets/add.html', {"form": AddOrEditForm()})


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, secret_name):
    secret = get_object_or_404(Secret, eap_username=secret_name)
    handler = EditHandler(request, secret)
    return handler.handle()
