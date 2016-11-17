import django_tables2 as tables
from django.template.loader import render_to_string
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper
# from ..forms import OverviewDetailForm


class PoolsTable(tables.Table):

    poolname = tables.Column(accessor="poolname", verbose_name="Name")
    addresses = tables.Column(accessor="addresses", verbose_name="Addresses")
    removebtn = tables.Column(accessor="id", verbose_name='Remove Pool', orderable=False)
    detail_collapse_column = tables.Column(accessor="id", verbose_name="", orderable=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        # self.pooldetail =  kwargs.pop("pooldetail")
        super(PoolsTable, self).__init__(*args, **kwargs)

    def render_removebtn(self, record):
        return render_to_string('pools/widgets/remove_column.html', {'poolname': record.poolname},
                                request=self.request)

    def render_poolname(self, record):
        return render_to_string('pools/widgets/name_column.html', {'record': record},
                                request=self.request)

    def render_detail_collapse_column(self, record):
        pools = ViciWrapper().get_pools()
        pool_details = {k: v for k, v in pools.items() if str(k) == str(record)}
        size = 0
        base = None
        online = 0
        offline = 0
        leases = None

        for key, value in pool_details[str(record)].items():
            if key == 'size':
                size = value
            elif key == 'base':
                base = value
            elif key == 'online':
                online = value
            elif key == 'offline':
                offline = value
            elif key == 'leases':
                leases = value
        return render_to_string('pools/widgets/detail_collapse_column.html', {'record': record, 'detail': pool_details,
                                                                              'size': size, 'base': base,
                                                                              'online': online, 'offline': offline,
                                                                              'leases': leases},
                                request=self.request)

    class Meta:
        attrs = {"class": "table"}

