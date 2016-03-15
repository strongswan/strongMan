from django.conf.urls import url

from . import views

app_name = 'connections'
urlpatterns = [
    url(r'create/0$', views.ChooseTypView.as_view(), name='connection_create'),
    url(r'create/1$', views.Ike2CertificateCreateView.as_view(), name='connection_create_certificate'),
    url(r'create/2$', views.Ike2EapCreateView.as_view(), name='connection_create_eap'),
    url(r'create/3$', views.Ike2CertificateCreateView.as_view(), name='connection_create_certificate'),
    url(r'create/4$', views.Ike2CertificateCreateView.as_view(), name='connection_create_certificate'),
    url(r'create/5$', views.Ike2CertificateCreateView.as_view(), name='connection_create_certificate'),
    url(r'update/1/(?P<pk>\d+)/$', views.Ike2CertificateUpdateView.as_view(), name='connection_update_certificate'),
    url(r'update/2/(?P<pk>\d+)/$', views.Ike2EapUpdateView.as_view(), name='connection_update_eap'),
    url(r'toggle/$', views.toggle_connection, name='connection_toggle'),
]
