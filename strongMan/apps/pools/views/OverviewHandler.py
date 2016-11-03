from django.contrib import messages
from django.shortcuts import render
from django_tables2 import RequestConfig
from strongMan.apps.pools.models import Pool
from strongMan.helper_apps.vici.wrapper.exception import ViciException
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper
from .. import tables


class OverviewHandler:
    def __init__(self, request):
        self.request = request
        self.ENTRIES_PER_PAGE = 50

    def handle(self):
        try:
            return self._render()
        except ViciException as e:
            messages.warning(self.request, str(e))

    def _render(self):
        queryset = Pool.objects.all()
        table = tables.PoolsTable(queryset, request=self.request)
        # vici_wrapper = ViciWrapper()
        # pools = vici_wrapper.get_pools()
        # detail_table = tables.DetailPoolTable(pools, request=self.request)
        RequestConfig(self.request, paginate={"per_page": self.ENTRIES_PER_PAGE}).configure(table)
        if len(queryset) == 0:
            table = None
        return render(self.request, 'pools/overview.html', {'table': table})
