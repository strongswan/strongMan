from django.http import Http404
from django.shortcuts import render
from . import models


def index(request):
    session = models.ViciSession()
    try:
        session.connect()
    except Exception:
        raise Http404("Could not connect to vici. Is ipsec running? Try ipsec start.")

    vici_info = session.info()
    return render(request, 'vici/view.html', {"vici_info": vici_info})

