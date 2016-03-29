from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import AddForm, CertificateSearchForm
from .models import Certificate
from .request_handler import AddHandler, DetailsHandler, OverviewHandler


@require_http_methods(["GET", "POST"])
def overview(request):
    handler = OverviewHandler(request, "all")
    return handler.handle()


@require_http_methods(["GET", "POST"])
def overview_ca(request):
    handler = OverviewHandler(request, "root")
    return handler.handle(filter_ca=True, should_ca=True)


@require_http_methods(["GET", "POST"])
def overview_certs(request):
    handler = OverviewHandler(request, "entities")
    return handler.handle(filter_ca=True, should_ca=False)


@require_http_methods(["GET", "POST"])
def add(request):
    if request.method == 'POST':
        handler = AddHandler.by_request(request)
        (request, html, context) = handler.handle()
        return render(request, html, context)
    elif request.method == 'GET':
        form = AddForm()
        return render(request, 'certificates/add.html', {"form": form})


@require_http_methods(["GET", "POST"])
def details(request, certificate_id):
    certificate = get_object_or_404(Certificate, id=certificate_id)
    handler = DetailsHandler(request, certificate)
    return handler.handle()
