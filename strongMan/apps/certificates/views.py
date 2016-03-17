from django.shortcuts import render
from .forms import AddHandler, AddForm
from .models import Certificate
from django.shortcuts import render


def overview(request):
    publics = Certificate.objects.all()
    return render(request, 'certificates/overview.html', {'publics': publics})


def overview_ca(request):
    publics = Certificate.objects.filter(is_CA=True)
    return render(request, 'certificates/overview.html', {'publics': publics})


def overview_certs(request):
    publics = Certificate.objects.filter(is_CA=False)
    return render(request, 'certificates/overview.html', {'publics': publics})


def add(request):
    if request.method == 'POST':
        handler = AddHandler.by_request(request)
        (request, html, context) = handler.handle()
        return render(request, html, context)
    elif request.method == 'GET':
        form = AddForm()
        return render(request, 'certificates/add.html', {"form": form})






