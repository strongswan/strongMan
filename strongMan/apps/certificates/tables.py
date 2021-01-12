import django_tables2 as tables
from django.template.loader import render_to_string
from .models import ViciCertificate


class UserCertificateTable(tables.Table):
    name = tables.Column(accessor="subject__cname", verbose_name='Name')
    subject = tables.Column(verbose_name="DistinguishedName",
                            attrs={'th': {'class': "hidden-sm hidden-xs"},
                                   'td': {'class': "hidden-sm hidden-xs"}})
    has_private_key = tables.BooleanColumn(orderable=False)
    removebtn = tables.Column(accessor="id", verbose_name='Remove', orderable=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(UserCertificateTable, self).__init__(*args, **kwargs)

    def render_name(self, record):
        return render_to_string('certificates/widgets/name_column.html', {'record': record},
                                request=self.request)

    def render_has_private_key(self, value):
        if value:
            return "Yes"
        else:
            return "No"

    def render_removebtn(self, record):
        is_vici = isinstance(record, ViciCertificate)
        return render_to_string('certificates/widgets/remove_column.html',
                                {'id': record.id, "is_vici": is_vici}, request=self.request)

    class Meta(object):
        attrs = {"class": "table table-striped"}
