from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from .CreateHandler import AddHandler
from .UpdateHandler import UpdateHandler
from .OverviewHandler import OverviewHandler
from .DeleteHandler import DeleteHandler
from .ToggleHandler import ToggleHandler
from .StateHandler import StateHandler
from .LogHandler import LogHandler
from .SaInfoHandler import SaInfoHandler
from .CertificatePickerHandler import CertificatePickerHandler
from .CaPickerHandler import CaPickerHandler


@require_http_methods('GET')
@login_required
def overview(request):
    handler = OverviewHandler(request)
    return handler.handle()


@login_required
@require_http_methods(['POST', 'GET'])
def create(request):
    handler = AddHandler(request)
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
@require_http_methods('POST')
def get_state(request, id):
    handler = StateHandler(request, id)
    return handler.handle()


@login_required
@require_http_methods('POST')
def get_log(request):
    handler = LogHandler(request)
    return handler.handle()


@login_required
@require_http_methods('POST')
def get_sa_info(request):
    handler = SaInfoHandler(request)
    return handler.handle()


@login_required
@require_http_methods(['POST'])
def get_certificatepicker(request):
    handler = CertificatePickerHandler(request)
    return handler.handle()


@login_required
@require_http_methods(['POST'])
def get_capicker(request):
    handler = CaPickerHandler(request)
    return handler.handle()


def _get_title(form):
    return form.get_choice_name()


def _get_type_name(cls):
    return type(cls).__name__
