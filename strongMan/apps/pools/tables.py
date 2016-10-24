import django_tables2 as tables
from django.template.loader import render_to_string


class PoolsTable(tables.Table):
    name = tables.Column(accessor="profile", verbose_name='Name')
    addresses = tables.Column(accessor="addresses.first.value", verbose_name="Server", orderable=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(PoolsTable, self).__init__(*args, **kwargs)

    def render_name(self, record):
        return render_to_string('pools/widgets/name_column.html', {'record': record}, request=self.request)

    def render_state(self, record):
        return render_to_string('pools/widgets/state_column.html', {'record': record}, request=self.request)

    class Meta:
        attrs = {"class": "table"}
