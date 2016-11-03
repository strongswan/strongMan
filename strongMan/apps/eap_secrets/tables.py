import django_tables2 as tables
from django.template.loader import render_to_string
from strongMan.apps.server_connections.models import EapAuthentication, EapTlsAuthentication


class EapSecretsTable(tables.Table):
    detail_collapse_column = tables.Column(accessor="id", verbose_name="", orderable=False)
    name = tables.Column(accessor="username", verbose_name='Name')
    type = tables.Column(accessor="type", verbose_name='Type')
    removebtn = tables.Column(accessor="id", verbose_name='Remove', orderable=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(EapSecretsTable, self).__init__(*args, **kwargs)

    def render_detail_collapse_column(self, record):
        counter = 0
        counter += record.eap_secret.all().count()
        counter += record.eap_tls_secret.all().count()
        # counter += EapAuthentication.objects.filter(secret=record.id).count()
        # counter += EapTlsAuthentication.objects.filter(secret=record.id).count()
        return render_to_string('eap_secrets/widgets/detail_collapse_column.html',
                                {'record': record, 'counter': counter}, request=self.request)

    def render_name(self, record):
        return render_to_string('eap_secrets/widgets/name_column.html', {'name': record.username}, request=self.request)

    def render_removebtn(self, record):
        return render_to_string('eap_secrets/widgets/remove_column.html', {'name': record.username},
                                request=self.request)

    class Meta:
        attrs = {"class": "table"}
