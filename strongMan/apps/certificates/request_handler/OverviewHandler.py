from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.contrib import messages

from ..forms import CertificateSearchForm
from .. import models
from ..services import ViciCertificateManager
from ...vici.wrapper.exception import ViciSocketException
import string


class AbstractOverviewHandler:
    def __init__(self):
        self.request = None
        self.ENTRIES_PER_PAGE = 10

    @classmethod
    def by_request(cls, request):
        handler = cls()
        handler.request = request
        return handler

    def page_tag(self):
        raise NotImplementedError()

    def all_certificates(self):
        '''
        Returns all possible certificates. Can raise a OvervieHandlerException
        '''
        raise NotImplementedError()

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

    def _search_for(self, all_certs, search_text):
        identities = models.AbstractIdentity.all_identities()
        cert_ids = []
        for ident in identities:
            if search_text in str(ident).lower():
                cert_ids.append(ident.certificate.id)
        return all_certs.filter(id__in=cert_ids)

    def handle(self):
        try:
            all_certs = self.all_certificates()
        except OverviewHandlerException as e:
            messages.add_message(self.request, messages.WARNING, str(e))
            return self._render()

        if self.request.method == "GET":
            return self._render(all_certs)

        form = CertificateSearchForm(self.request.POST)
        if not form.is_valid():
            return self._render(all_certs)

        search_pattern = form.cleaned_data["search_text"]
        search_result = self._search_for(all_certs,search_pattern)
        page = form.cleaned_data["page"]
        return self._render(search_result, page, search_pattern)

    def _render(self, certificates=[], page=1, search_pattern=""):
        x509_list = self._paginate(certificates, page=page)
        return render(self.request, 'certificates/overview.html',
                      {'publics': x509_list, "view": self.page_tag(), "search_pattern": search_pattern})


class ViciOverviewHandler(AbstractOverviewHandler):
    def page_tag(self):
        return "vici"

    def all_certificates(self):
        try:
            ViciCertificateManager.reload_certs()
        except ViciSocketException as e:
            raise OverviewHandlerException("Vici is not reachable!") from e
        return models.ViciCertificate.objects.all()


class EntityOverviewHandler(AbstractOverviewHandler):
    def page_tag(self):
        return "entities"

    def all_certificates(self):
        return models.UserCertificate.objects.filter(is_CA=False)


class MainOverviewHandler(AbstractOverviewHandler):
    def page_tag(self):
        return "all"

    def all_certificates(self):
        return models.UserCertificate.objects.all()


class RootOverviewHandler(AbstractOverviewHandler):
    def page_tag(self):
        return "root"

    def all_certificates(self):
        return models.UserCertificate.objects.filter(is_CA=True)

class OverviewHandlerException(Exception):
    pass