import django_tables2 as tables
from django.template.loader import render_to_string


class ConnectionTable(tables.Table):
    name = tables.Column(accessor="profile", verbose_name='Name')
    gateway = tables.Column(accessor="remote_addresses__first__value", verbose_name="Server",
                            orderable=False)
    typ = tables.Column(accessor="subclass__choice_name", verbose_name="Typ", orderable=False)
    state = tables.Column(accessor="state", verbose_name="State", orderable=False,
                          attrs={'th': {'class': "text-right"}, 'td': {'class': "text-right"}})

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(ConnectionTable, self).__init__(*args, **kwargs)

    def render_name(self, record):
        return render_to_string('connections/widgets/name_column.html', {'record': record},
                                request=self.request)

    def render_state(self, record):
        return render_to_string('connections/widgets/state_column.html', {'record': record},
                                request=self.request)

    class Meta(object):
        attrs = {"class": "table"}
