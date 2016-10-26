from django.contrib.auth.decorators import login_required
from django.shortcuts import render  # , get_object_or_404
from django.views.decorators.http import require_http_methods

from . import OverviewHandler
# from .DetailsHandler import DetailsHandler
from .AddHandler import AddHandler

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from . import OverviewHandler
from ..forms import AddForm
from .AddHandler import AddHandler



@login_required
@require_http_methods(["GET", "POST"])
def overview(request):
    handler = OverviewHandler.OverviewHandler.by_request(request)
    return handler.handle()

@login_required
@require_http_methods(["GET", "POST"])
def delete_secret(request, secret_id):
    handler = OverviewHandler.OverviewHandler.by_delete_request(request, secret_id)
    return handler.handle()

# @login_required
# @require_http_methods(["GET", "POST"])
# def details(request, eap_id):
#     handler = DetailsHandler(request, eap_id)
#     return handler.handle()

# @login_required
# @require_http_methods(["GET", "POST"])
# def overview_ca(request):
#     handler = OverviewHandler.RootOverviewHandler.by_request(request)
#     return handler.handle()
#
#
# @login_required
# @require_http_methods(["GET", "POST"])
# def overview_certs(request):
#     handler = OverviewHandler.EntityOverviewHandler.by_request(request)
#     return handler.handle()
#
#
# @login_required
# @require_http_methods(["GET", "POST"])
# def overview_vici(request):
#     handler = OverviewHandler.ViciOverviewHandler.by_request(request)
#     return handler.handle()


@login_required
@require_http_methods(["GET", "POST"])
def add(request):
    if request.method == 'POST':
        handler = AddHandler.by_request(request)
        (request, html, context) = handler.handle()
        return render(request, html, context)
    elif request.method == 'GET':
        return render(request, 'eap_secrets/add.html', {"form": AddForm()})

#
# @login_required
# @require_http_methods(["GET", "POST"])
# def add_form(request):
#     if request.method == 'POST':
#         handler = AddHandler.by_request(request, True)
#         (request, html, context) = handler.handle()
#         return render(request, html, context)
#     elif request.method == 'GET':
#         return render(request, 'certificates/add_form.html', {"form": AddForm()})
#

# @login_required
# @require_http_methods(["GET", "POST"])
# def details(request, certificate_id):
#     certificate = get_object_or_404(Certificate, id=certificate_id)
#     handler = DetailsHandler(request, certificate)
#     return handler.handle()
