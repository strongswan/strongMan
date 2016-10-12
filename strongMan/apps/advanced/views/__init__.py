from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .AdvancedHandler import ProHandler


@login_required
@require_http_methods('GET')
def promode(request):
    handler = ProHandler(request)
    return handler.handle()
