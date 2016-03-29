from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render, HttpResponseRedirect

from.models import Certificate, Domain
from .container import ContainerTypes
from .forms import AddForm, CertificateSearchForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from oscrypto.errors import AsymmetricKeyError

class OverviewHandler:
    def __init__(self, request, page_tag):
        self.request = request
        self.page_tag = page_tag
        self.ENTRIES_PER_PAGE = 10

    def _all_certificates(self, filter_ca=False, should_ca=False):
        if not filter_ca:
            return Certificate.objects.all()
        else:
            return Certificate.objects.filter(is_CA=should_ca)

    def _search_for(self, search_pattern, filter_ca=False, should_ca=False):
        '''
        Searches for certificates in valid_domains
        :param search_pattern: Search text to filter for
        :param filter_ca: Should result additionaly be filtered by is_CA?
        :param should_CA: Only affects the result if filter_ca=True
        :return: [Certificate]
        '''
        if search_pattern == "":
            return self._all_certificates(filter_ca=filter_ca, should_ca=should_ca)
        domains = Domain.objects.filter(value__contains=search_pattern)
        certs = []
        for domain in domains:
            cert = domain.certificate
            if not cert in certs:
                if filter_ca:
                    if cert.is_CA == should_ca:
                        certs.append(cert)
                else:
                    certs.append(cert)
        return certs

    def _paginate(self, certificate_list, page=1):
        paginator = Paginator(certificate_list, self.ENTRIES_PER_PAGE)
        try:
            x509_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            x509_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            x509_list = paginator.page(paginator.num_pages)
        return x509_list

    def handle(self, filter_ca=False, should_ca=False):
        search_pattern = ""
        page = 1
        if self.request.method == "GET":
            publics = self._all_certificates(filter_ca=filter_ca, should_ca=should_ca)
        else:
            form = CertificateSearchForm(self.request.POST)
            if not form.is_valid():
                publics = self._all_certificates(filter_ca=filter_ca, should_ca=should_ca)
            else:
                search_pattern = form.cleaned_data["search_text"]
                publics = self._search_for(search_pattern=search_pattern, filter_ca=filter_ca, should_ca=should_ca)
                page = form.cleaned_data["page"]
        x509_list = self._paginate(publics, page=page)
        return render(self.request, 'certificates/overview.html',
                      {'publics': x509_list, "view": self.page_tag, "search_pattern": search_pattern})

class DetailsHandler:
    def __init__(self, request, certificate_object):
        self.request = request
        self.certificate = certificate_object

    def _render_detail(self):
        if self.certificate.private_key is None:
            return render(self.request, 'certificates/edit.html', {"certificate": self.certificate})
        else:
            return render(self.request, 'certificates/edit.html',
                          {"certificate": self.certificate, 'private': self.certificate.private_key})

    def _remove_certificate(self):
        cname = self.certificate.subject.cname
        self.certificate.delete()
        return cname

    def _remove_privatekey(self):
        private = self.certificate.private_key
        self.certificate.private_key = None
        self.certificate.save()
        privatekey_has_another_certificate = private.certificates.all().__len__() > 1
        if not privatekey_has_another_certificate:
            private.delete()

    def handle(self):
        if self.request.method == "GET":
            return self._render_detail()
        elif self.request.method == "POST":
            if "remove_cert" in self.request.POST:
                cname = self._remove_certificate()
                messages.add_message(self.request, messages.INFO, "Certificate " + cname + " has been removed.")
                return HttpResponseRedirect(reverse('certificates:overview'))
            elif "remove_privatekey" in self.request.POST:
                self._remove_privatekey()
                messages.add_message(self.request, messages.INFO, "Private key has been removed.")
                return self._render_detail()
        return self._render_detail()


class AddHandler:
    def __init__(self):
        self.form = None
        self.request = None

    @classmethod
    def by_request(cls, request):
        handler = cls()
        handler.request = request
        return handler

    def handle(self):
        '''
        Handles a Add Container request. Adds the specific container to the database
        :return: a rendered site specific for the request
        '''
        self.form = AddForm(self.request.POST, self.request.FILES)
        if not self.form.is_valid():
            messages.add_message(self.request, messages.ERROR,
                                 'No valid container detected. Maybe your container needs a password?')
            return self.request, 'certificates/add.html', {"form": self.form}

        try:
            type = self.form.detect_container_type()
            if type == ContainerTypes.X509:
                return self._handle_x509()

            elif type == ContainerTypes.PKCS1 or type == ContainerTypes.PKCS8:
                return self._handle_privatekey()

            elif type == ContainerTypes.PKCS12:
                return self._handle_pkcs12()
        except (ValueError, TypeError, AsymmetricKeyError, OSError) as e:
            messages.add_message(self.request, messages.ERROR,
                                 "Error reading file. Maybe your file is corrupt?")
            return self.request, 'certificates/add.html', {"form": self.form}
        except Exception as e:
            messages.add_message(self.request, messages.ERROR,
                                 "Internal error: " + str(e))
            return self.request, 'certificates/add.html', {"form": self.form}

    def _handle_x509(self):
        x509 = self.form.to_publickey()
        if x509.already_exists():
            messages.add_message(self.request, messages.WARNING,
                                 'Certificate ' + x509.subject.cname + ' has already existed!')
        else:
            x509.save_new()
        return self.request, 'certificates/added.html', {"public": x509}

    def _handle_privatekey(self):
        private = self.form.to_privatekey()
        if not private.certificate_exists():
            messages.add_message(self.request, messages.Error, 'No certificate exists for this private key. '
                                                               'Upload certificate first!')
            return self.request, 'certificates/add.html'

        if private.already_exists():
            private = private.get_existing_privatekey()
            messages.add_message(self.request, messages.WARNING, 'Private key has already existed!')
        else:
            private.save()
            private.connect_to_certificates()
        public = private.certificates.all()[0]
        return self.request, 'certificates/added.html', {"private": private, "public": public}

    def _handle_pkcs12(self):
        private = self.form.to_privatekey()
        public = self.form.to_publickey()
        further_publics = self.form.further_publics()

        if public.already_exists():
            messages.add_message(self.request, messages.WARNING,
                                 'Certificate ' + public.subject.cname + ' has already existed!')
        else:
            public.save_new()

        if private.already_exists():
            messages.add_message(self.request, messages.WARNING, 'Private key has already existed!')
        else:
            private.save()
            private.connect_to_certificates()

        for cert in further_publics:
            if cert.already_exists():
                messages.add_message(self.request, messages.WARNING,
                                     'Certificate ' + cert.subject.cname + ' has already existed!')
            else:
                cert.save_new()

        return self.request, 'certificates/added.html', {"private": private, "public": public,
                                                         "further_publics": further_publics}
