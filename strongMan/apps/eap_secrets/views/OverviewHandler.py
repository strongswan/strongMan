from django.contrib import messages
from django.shortcuts import render
from django_tables2 import RequestConfig

from ...server_connections import models
from ..forms import EapSecretSearchForm
from ..tables import EapSecretsTable
from ...server_connections.models import Secret


class OverviewHandler:
    def __init__(self):
        self.request = None
        self.delete_id = None
        self.ENTRIES_PER_PAGE = 10

    @classmethod
    def by_request(cls, request):
        handler = cls()
        handler.request = request
        return handler

    @classmethod
    def by_delete_request(cls, request, delete_id):
        handler = cls()
        handler.request = request
        handler.delete_id = delete_id
        return handler

    def page_tag(self):
        return "all"

    def all_secrets(self):
        return models.Secret.objects.all()

    def _search_for(self, all_secrets, search_text):
        '''
        Searches for keywords in Secrets
        :param all_secrets: prefiltered list of eap secrets
        :param search_text: text to search for
        :return: queryset of filtered secrets
        '''
        secret_ids = []
        secrets = models.secret.objects.all()
        for secret in secrets:
            if search_text.lower() in str(secret.authentication.name).lower():
                secret_ids.append(secret.pk)
        return all_secrets.filter(pk__in=secret_ids)

    def _render(self, queryset=Secret.objects.none(), search_pattern=""):
        table = EapSecretsTable(queryset, request=self.request)
        RequestConfig(self.request, paginate={"per_page": self.ENTRIES_PER_PAGE}).configure(table)
        if len(queryset) == 0:
            table = None
        return render(self.request, 'eap_secrets/overview.html',
                      {'table': table, "view": self.page_tag(), "search_pattern": search_pattern})

    def handle(self):
        try:
            if self.delete_id is not None:
                models.Secret.objects.get(pk__in=self.delete_id).delete()
            all_secrets = self.all_secrets()
        except OverviewHandlerException as e:
            messages.add_message(self.request, messages.WARNING, str(e))
            return self._render()

        if self.request.method == "GET":
            return self._render(all_secrets)

        form = EapSecretSearchForm(self.request.POST)
        if not form.is_valid():
            return self._render(all_secrets)

        search_pattern = form.cleaned_data["search_text"]
        if not search_pattern == '':
            search_result = self._search_for(all_secrets, search_pattern)
        else:
            search_result = all_secrets
        return self._render(search_result, search_pattern)


class OverviewHandlerException(Exception):
    pass
