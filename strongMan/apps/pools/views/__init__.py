from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from .OverviewHandler import OverviewHandler
from ..forms import AddForm
from .AddHandler import AddHandler


@login_required
@require_http_methods(["GET", "POST"])
def add(request):
    if request.method == 'POST':
        handler = AddHandler.by_request(request)
        (request, html, context) = handler.handle()
        return render(request, html, context)
    elif request.method == 'GET':
        return render(request, 'pools/add.html', {"form": AddForm()})


@require_http_methods('GET')
@login_required
def overview(request):
    handler = OverviewHandler(request)
    return handler.handle()


def _get_title(form):
    return form.get_choice_name()


def _get_type_name(cls):
    return type(cls).__name__
