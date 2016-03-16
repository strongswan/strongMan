from django.views.generic.edit import CreateView, UpdateView
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from .forms import AddCertificatesForm
from django.contrib import messages
from django.views import generic
from .container import ContainerTypes
from .models import PublicKey


def add(request):
    if request.method == 'POST':
        form = AddCertificatesForm(request.POST, request.FILES)
        if form.is_valid():
            type = form.detect_container_type()
            if type == ContainerTypes.X509:
                x509 = form.to_publickey()
                return handle_x509(request, x509)
            elif type == ContainerTypes.PKCS1 or type == ContainerTypes.PKCS8:
                private = form.to_privatekey()
                return handle_privatekey(request,private)
            elif type == ContainerTypes.PKCS12:
                private = form.to_privatekey()
                public = form.to_publickey()
                further_publics = form.further_publics()
                return handle_pkcs12(request, private,public, further_publics)

        else:
            messages.add_message(request, messages.ERROR, 'No valid container detected. Maybe your container needs a password?')
            return render(request, 'certificates/add.html', {"form": form})

    elif request.method == 'GET':
        form = AddCertificatesForm()
        return render(request, 'certificates/add.html', {"form": form})


def handle_x509(request, x509):
    if x509.already_exists():
        messages.add_message(request, messages.WARNING, 'Certificate ' + x509.subject.cname + ' has already existed!')
    else:
        x509.save_new()
    return render(request, 'certificates/added.html', {"public": x509})


def handle_privatekey(request, private):
    public = private.publickey()
    if public == None:
        messages.add_message(request, messages.Error, 'No certificate exists for this private key. Upload certificate first!')
        return render(request, 'certificates/add.html')

    if private.already_exists():
        messages.add_message(request, messages.WARNING, 'Private key has already existed!')
    else:
        private.save_new(public)
    return render(request, 'certificates/added.html', {"private": private, "public": public})


def handle_pkcs12(request, private, public, further_publics):
    if public.already_exists():
        messages.add_message(request, messages.WARNING, 'Certificate ' + public.subject.cname + ' has already existed!')
    else:
        public.save_new()

    if private.already_exists():
        messages.add_message(request, messages.WARNING, 'Private key has already existed!')
    else:
        private.save_new(public)
    from .container import X509Container
    for cert in further_publics:
        if cert.already_exists():
            messages.add_message(request, messages.WARNING, 'Certificate ' + cert.subject.cname + ' has already existed!')
        else:
            cert.save_new()

    return render(request, 'certificates/added.html', {"private": private, "public": public, "further_publics": further_publics})



