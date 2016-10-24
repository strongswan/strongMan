import django_tables2 as tables
from django.template.loader import render_to_string


class EapSecretsTable(tables.Table):
    name = tables.Column()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(EapSecretsTable, self).__init__(*args, **kwargs)