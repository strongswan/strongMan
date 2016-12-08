from django.contrib import messages
from django.shortcuts import render
from django_tables2 import RequestConfig
from strongMan.apps.pools.models import Pool
from strongMan.helper_apps.vici.wrapper.exception import ViciException
from .. import tables
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper


class PoolRefreshHandler:
    def __init__(self, request):
        self.request = request
        self.ENTRIES_PER_PAGE = 50

    def handle(self):
        try:
            return self._render()
        except ViciException as e:
            messages.warning(self.request, str(e))

    def _render(self):
        pooldetails = ViciWrapper().get_pools({'leases': "yes"})
        table = {"pools": pooldetails}
        return render(self.request, 'pools/widgets/detailPoolTable.html', {'table': table, 'is_refresh': True})
