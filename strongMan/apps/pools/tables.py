import django_tables2 as tables
from django.template.loader import render_to_string


class PoolsTable(tables.Table):
    poolname = tables.Column(accessor="poolname", verbose_name="Name")
    addresses = tables.Column(accessor="addresses", verbose_name="Addresses")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(PoolsTable, self).__init__(*args, **kwargs)

    class Meta:
        attrs = {"class": "table"}
