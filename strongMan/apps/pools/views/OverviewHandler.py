from django.contrib import messages
from django.shortcuts import render
from django_tables2 import RequestConfig
from strongMan.apps.pools.models import Pool
from strongMan.helper_apps.vici.wrapper.exception import ViciException
from .. import tables
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper


class OverviewHandler(object):
    def __init__(self, request):
        self.request = request
        self.ENTRIES_PER_PAGE = 50

    def handle(self):
        try:
            return self._render()
        except ViciException as e:
            messages.warning(self.request, str(e))

    def _render(self):
        dhcpdbvalue = Pool.objects.all().filter(poolname__contains='dhcp')
        if not dhcpdbvalue:
            dhcppool = Pool(poolname='dhcp')
            dhcppool.clean()
            dhcppool.save()

        radiusdbvalue = Pool.objects.all().filter(poolname__contains='radius')
        if not radiusdbvalue:
            radiuspool = Pool(poolname='radius')
            radiuspool.clean()
            radiuspool.save()

        queryset = Pool.objects.exclude(poolname__contains='dhcp').exclude(poolname__contains='radius')
        pools = ViciWrapper().get_pools({'leases': "yes"})
        table = tables.PoolsTable(queryset, request=self.request, pools=pools)

        RequestConfig(self.request, paginate={"per_page": self.ENTRIES_PER_PAGE}).configure(table)
        if len(queryset) == 0:
            table = None
        return render(self.request, 'pools/overview.html', {'table': table})
