import django_tables2 as tables
from django.template.loader import render_to_string

class ConnectionTable(tables.Table):
    name = tables.Column(accessor="profile", verbose_name='Name')
    gateway = tables.Column(accessor="", verbose_name="Gateway")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(ConnectionTable, self).__init__(*args, **kwargs)

    class Meta:
        attrs = {"class": "table table-striped"}