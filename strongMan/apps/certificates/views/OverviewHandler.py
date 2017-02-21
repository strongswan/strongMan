from django.contrib import messages
from django.shortcuts import render
from django_tables2 import RequestConfig

from strongMan.helper_apps.vici.wrapper.exception import ViciSocketException
from .. import models
from ..forms import CertificateSearchForm
from ..models import UserCertificate
from ..services import ViciCertificateManager
from ..tables import UserCertificateTable


class AbstractOverviewHandler(object):
    def __init__(self):
        self.request = None
        self.ENTRIES_PER_PAGE = 10

    @classmethod
    def by_request(cls, request):
        handler = cls()
        handler.request = request
        return handler

    def page_tag(self):
        '''
        A string that identifies the view. This gets populated to the template.
        :return:
        '''
        raise NotImplementedError()

    def all_certificates(self):
        '''
        Returns all possible certificates. Can raise a OvervieHandlerException
        '''
        raise NotImplementedError()

    def _search_for(self, all_certs, search_text):
        '''
        Searches for keywords in certificates
        :param all_certs: prefiltered list of certificates
        :param search_text: text to search for
        :return: queryset of filtered certificates
        '''
        cert_ids = []
        cert_ids += self._search_for_indentities(search_text)
        cert_ids += self._search_for_nicknames(all_certs, search_text)
        return all_certs.filter(pk__in=cert_ids)

    def _search_for_indentities(self, search_text):
        '''
        Searches for keywords in identities
        :param search_text: text to search for
        :return: list of certificate id's
        '''
        cert_ids = []
        identities = models.identities.AbstractIdentity.objects.all()
        identities = models.identities.AbstractIdentity.subclasses(identities)
        for ident in identities:
            if search_text.lower() in str(ident).lower():
                cert_ids.append(ident.certificate.pk)
        return cert_ids

    def _search_for_nicknames(self, all_certs, search_text):
        '''
        Searches for keywords in nicknames
        :param all_certs: list of prefiltered certificates
        :param search_text: text to search for
        :return: list of certificate id's
        '''
        cert_ids = []

        for cert in all_certs:
            if search_text.lower() in cert.nickname.lower():
                cert_ids.append(cert.pk)
        return cert_ids

    def _render(self, queryset=UserCertificate.objects.none(), search_pattern=""):
        table = UserCertificateTable(queryset, request=self.request)
        RequestConfig(self.request, paginate={"per_page": self.ENTRIES_PER_PAGE}).configure(table)
        if len(queryset) == 0:
            table = None
        return render(self.request, 'certificates/overview.html',
                      {'table': table, "view": self.page_tag(), "search_pattern": search_pattern})

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
        if not search_pattern == '':
            search_result = self._search_for(all_certs, search_pattern)
        else:
            search_result = all_certs
        return self._render(search_result, search_pattern)


class ViciOverviewHandler(AbstractOverviewHandler):
    def page_tag(self):
        return "vici"

    def all_certificates(self):
        try:
            ViciCertificateManager.reload_certs()
        except ViciSocketException:
            return []
        return models.certificates.ViciCertificate.objects.all()


class EntityOverviewHandler(AbstractOverviewHandler):
    def page_tag(self):
        return "entities"

    def all_certificates(self):
        return models.certificates.UserCertificate.objects.filter(is_CA=False)


class MainOverviewHandler(AbstractOverviewHandler):
    def page_tag(self):
        return "all"

    def all_certificates(self):
        return models.certificates.UserCertificate.objects.all()


class RootOverviewHandler(AbstractOverviewHandler):
    def page_tag(self):
        return "root"

    def all_certificates(self):
        return models.certificates.UserCertificate.objects.filter(is_CA=True)


class OverviewHandlerException(Exception):
    pass
