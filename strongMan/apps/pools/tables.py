import django_tables2 as tables
from django.template.loader import render_to_string


class PoolsTable(tables.Table):
    detail_collapse_column = tables.Column(accessor="id", verbose_name="", orderable=False)
    poolname = tables.Column(accessor="poolname", verbose_name="Name")
    addresses = tables.Column(accessor="addresses", verbose_name="Addresses")
    removebtn = tables.Column(accessor="id", verbose_name='Remove Pool', orderable=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.pools = kwargs.pop("pools")
        super(PoolsTable, self).__init__(*args, **kwargs)

    def render_removebtn(self, record):
        return render_to_string('pools/widgets/remove_column.html', {'poolname': record.poolname},
                                request=self.request)

    def render_poolname(self, record):
        return render_to_string('pools/widgets/name_column.html', {'record': record},
                                request=self.request)

    def render_detail_collapse_column(self, record):
        return render_to_string('pools/widgets/detail_collapse_column.html', {'record': record},
                                request=self.request)

    class Meta(object):
        attrs = {"class": "table"}
