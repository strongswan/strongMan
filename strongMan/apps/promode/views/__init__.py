from django.views.decorators.http import require_http_methods
from .ProHandler import ProHandler


@require_http_methods('GET')
def promode(request):
    handler = ProHandler(request)
    return handler.handle()
