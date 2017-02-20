import django_tables2 as tables
from django.template.loader import render_to_string


class EapSecretsTable(tables.Table):
    name = tables.Column(accessor="username", verbose_name='Name')
    type = tables.Column(accessor="type", verbose_name='Type')
    removebtn = tables.Column(accessor="id", verbose_name='Remove', orderable=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(EapSecretsTable, self).__init__(*args, **kwargs)

    def render_name(self, record):
        return render_to_string('eap_secrets/widgets/name_column.html', {'name': record.username},
                                request=self.request)

    def render_removebtn(self, record):
        return render_to_string('eap_secrets/widgets/remove_column.html', {'name': record.username},
                                request=self.request)

    class Meta(object):
        attrs = {"class": "table"}
