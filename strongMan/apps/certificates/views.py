from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods

from .forms import AddForm, CertificateSearchForm
from .models import Certificate
from .request_handler import AddHandler, DetailsHandler


@require_http_methods(["GET", "POST"])
def overview(request):
    search_pattern = ""
    if request.method == "GET":
        publics = Certificate.objects.all()
    elif request.method == "POST":
        form = CertificateSearchForm(request.POST)
        if not form.is_valid():
            publics = Certificate.objects.all()
        else:
            publics = form.search_for()
            search_pattern = form.cleaned_data["search_text"]
    return render(request, 'certificates/overview.html', {'publics': publics, "view": "all", "search_pattern": search_pattern})


@require_http_methods(["GET", "POST"])
def overview_ca(request):
    search_pattern = ""
    if request.method == "GET":
        publics = Certificate.objects.filter(is_CA=True)
    elif request.method == "POST":
        form = CertificateSearchForm(request.POST)
        if not form.is_valid():
            publics = Certificate.objects.filter(is_CA=True)
        else:
            publics = form.search_for(filter_ca=True, should_CA=True)
            search_pattern = form.cleaned_data["search_text"]
    return render(request, 'certificates/overview.html', {'publics': publics, "view": "root", "search_pattern": search_pattern})


@require_http_methods(["GET", "POST"])
def overview_certs(request):
    search_pattern = ""
    if request.method == "GET":
        publics = Certificate.objects.filter(is_CA=False)
    elif request.method == "POST":
        form = CertificateSearchForm(request.POST)
        if not form.is_valid():
            publics = Certificate.objects.filter(is_CA=False)
        else:
            publics = form.search_for(filter_ca=True, should_CA=False)
            search_pattern = form.cleaned_data["search_text"]
    return render(request, 'certificates/overview.html', {'publics': publics, "view": "entities", "search_pattern": search_pattern})


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
