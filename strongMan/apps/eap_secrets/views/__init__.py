from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404


from .OverviewHandler import OverviewHandler
from .AddHandler import AddHandler
from .EditHandler import EditHandler
from ..models import Secret


@login_required
@require_http_methods(["GET", "POST"])
def overview(request):
    handler = OverviewHandler.by_request(request)
    return handler.handle()


@login_required
@require_http_methods(["GET", "POST"])
def add(request):
    handler = AddHandler.by_request(request)
    return handler.handle()


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, secret_name):
    secret = get_object_or_404(Secret, username=secret_name)
    handler = EditHandler(request, secret)
    return handler.handle()
