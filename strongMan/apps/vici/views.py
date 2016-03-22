import pprint
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
#from .models import CertReader
from .forms import UploadFileForm, UploadFile
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from .certs.help import print_dict

from . import models


def index(request):
    session = models.ViciSession()
    try:
        session.connect()
    except Exception:
        raise Http404("Could not connect to vici. Is ipsec running? Try ipsec start.")

    vici_info = session.info()
    return render(request, 'vici/view.html', {"vici_info": vici_info})


def certificate(request):
    ret = "<html><head/><body>"
    ret += "<h2>X509 PEM</h2>"

    ret += "<h2>RSA PEM</h2>"

    ret += "</body></html>"
    return HttpResponse(ret)


def add_conn(request):
    from .vici import Session as vici_session
    import socket
    sock = socket.socket(socket.AF_UNIX)
    sock.connect("/var/run/charon.vici")
    session = vici_session(sock)
    conns = session.list_conns()

    if request.method == "GET":
        return render(request, 'vici/addconn.html')
    if request.method == "POST":
        config = ""
        try:
            config = request.POST['config']
        except Exception:
            return render(request, 'vici/addconn.html', {'error_message': "Failure happend..."})
        print(config)
        session = models.ViciSession()
        session.connect()
        test = {'test':{}}
        result = session.session.load_conn(test)
        print(result)
        return HttpResponseRedirect("/vici/")
    else:
        raise Http404("Only GET or POST possible.")


def cert_upload(request):
    '''
    context = {'uploaded': False,}
    if request.method == 'POST':
        file1 = request.FILES['myfile1']
        file2 = request.FILES['myfile2']
        ident1, value1 = get_ident2(file1.read())
        ident2, value2 = get_ident2(file2.read())

        equal = ident1 == ident2
        context = {'uploaded': True, 'filename1': str(file1), 'filename2': str(file2), 'equal': equal,
                   'value1': print_dict(value1, newline="\n"), 'value2': print_dict(value2, newline="\n")}
    '''
    # Render list page with the documents and the form
    return render(request, 'vici/certificate_equal.html', context)


def get_ident2(bytes, pw=None):
    """

    Args:
        bytes:
        pw:

    Returns:

    """
    reader = CertReader.by_bytes(bytes)
    if pw == None:
        reader.detect_type()
    else:
        reader.detect_type(pw)

    return (str(reader.public_key_hash()), reader.asn1.native)
