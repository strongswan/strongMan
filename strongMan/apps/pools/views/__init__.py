from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from .OverviewHandler import OverviewHandler
from ..forms import AddOrEditForm
from .AddHandler import AddHandler
from django.shortcuts import render, get_object_or_404
from .EditHandler import EditHandler
from ..models import Pool

@login_required
@require_http_methods(["GET", "POST"])
def add(request):
    if request.method == 'POST':
        handler = AddHandler.by_request(request)
        return handler.handle()
    elif request.method == 'GET':
        return render(request, 'pools/add.html', {"form": AddOrEditForm()})


@require_http_methods('GET')
@login_required
def overview(request):
    handler = OverviewHandler(request)
    return handler.handle()


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, poolname):
    pool = get_object_or_404(Pool, poolname=poolname)
    handler = EditHandler(request, pool)
    return handler.handle()


def _get_title(form):
    return form.get_choice_name()


def _get_type_name(cls):
    return type(cls).__name__
