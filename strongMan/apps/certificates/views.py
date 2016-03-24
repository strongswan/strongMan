from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods

from .forms import AddForm, CertificateSearchForm
from .models import Certificate
from .request_handler import AddHandler, DetailsHandler


@require_http_methods(["GET", "POST"])
def overview(request):
    if request.method == "GET":
        publics = Certificate.objects.all()
    elif request.method == "POST":
        form = CertificateSearchForm(request.POST)
        if not form.is_valid():
            publics = Certificate.objects.all()
        else:
            publics = form.search_for()
    return render(request, 'certificates/overview.html', {'publics': publics})


@require_http_methods(["GET", "POST"])
def overview_ca(request):
    if request.method == "GET":
        publics = Certificate.objects.filter(is_CA=True)
    elif request.method == "POST":
        form = CertificateSearchForm(request.POST)
        if not form.is_valid():
            publics = Certificate.objects.filter(is_CA=True)
        else:
            publics = form.search_for(filter_ca=True, should_CA=True)
    return render(request, 'certificates/overview.html', {'publics': publics})


@require_http_methods(["GET", "POST"])
def overview_certs(request):
    if request.method == "GET":
        publics = Certificate.objects.filter(is_CA=False)
    elif request.method == "POST":
        form = CertificateSearchForm(request.POST)
        if not form.is_valid():
            publics = Certificate.objects.filter(is_CA=False)
        else:
            publics = form.search_for(filter_ca=True, should_CA=False)
    return render(request, 'certificates/overview.html', {'publics': publics})


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
