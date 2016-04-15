from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods

from strongMan.apps.certificates.models.certificates import Certificate
from strongMan.apps.certificates.request_handler import OverviewHandler
from strongMan.apps.certificates.request_handler.DetailsHandler import DetailsHandler
from .forms import AddForm
from .request_handler.AddHandler import AddHandler


@login_required
@require_http_methods(["GET", "POST"])
def overview(request):
    handler = OverviewHandler.MainOverviewHandler.by_request(request)
    return handler.handle()


@login_required
@require_http_methods(["GET", "POST"])
def overview_ca(request):
    handler = OverviewHandler.RootOverviewHandler.by_request(request)
    return handler.handle()


@login_required
@require_http_methods(["GET", "POST"])
def overview_certs(request):
    handler = OverviewHandler.EntityOverviewHandler.by_request(request)
    return handler.handle()


@login_required
@require_http_methods(["GET", "POST"])
def overview_vici(request):
    handler = OverviewHandler.ViciOverviewHandler.by_request(request)
    return handler.handle()


@login_required
@require_http_methods(["GET", "POST"])
def add(request):
    if request.method == 'POST':
        handler = AddHandler.by_request(request)
        (request, html, context) = handler.handle()
        return render(request, html, context)
    elif request.method == 'GET':
        form = AddForm()
        return render(request, 'certificates/add.html', {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def details(request, certificate_id):
    certificate = get_object_or_404(Certificate, id=certificate_id)
    handler = DetailsHandler(request, certificate)
    return handler.handle()
