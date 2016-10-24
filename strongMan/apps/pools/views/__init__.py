from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from .OverviewHandler import OverviewHandler


@require_http_methods('GET')
@login_required
def overview(request):
    handler = OverviewHandler(request)
    return handler.handle()


def _get_title(form):
    return form.get_choice_name()


def _get_type_name(cls):
    return type(cls).__name__
