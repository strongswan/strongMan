from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods


from .request_handler.CreateHandler import CreateHandler
from .request_handler.UpdateHandler import UpdateHandler
from .request_handler.OverviewHandler import OverviewHandler
from .request_handler.DeleteHandler import DeleteHandler
from .request_handler.ToggleHandler import ToggleHandler
from .request_handler.StateHandler import StateHandler


@require_http_methods('GET')
@login_required
def overview(request):
    handler = OverviewHandler(request)
    return handler.handle()


@login_required
@require_http_methods(['POST', 'GET'])
def create(request):
    handler = CreateHandler(request)
    return handler.handle()


@login_required
def update(request, id):
    handler = UpdateHandler(request, id)
    return handler.handle()



@login_required
@require_http_methods('POST')
def toggle_connection(request):
    handler = ToggleHandler(request)
    return handler.handle()


@login_required
def delete_connection(request, id):
    handler = DeleteHandler(request, id)
    return handler.handle()


@login_required
def get_state(request, id):
    handler = StateHandler(request, id)
    return handler.handle()


def _get_title(form):
    return form.get_choice_name()


def _get_type_name(cls):
    return type(cls).__name__
