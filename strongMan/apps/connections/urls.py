from django.conf.urls import url

from . import views

app_name = 'connections'
urlpatterns = [
    url(r'^$', views.overview, name='index'),
    url(r'^add/$', views.create, name='choose'),
    url(r'^(?P<id>\d+)/$', views.update, name='update'),
    url(r'delete/(?P<id>\d+)/$', views.delete_connection, name='delete'),
    url(r'state/(?P<id>\d+)/$', views.get_state, name='state'),
    url(r'log/$', views.get_log, name='log'),
    url(r'toggle/$', views.toggle_connection, name='toggle'),
    url(r'info/$', views.get_sa_info, name='info'),
    url(r'identities/$', views.get_identities, name='identities'),
    url(r'certificatepicker/$', views.get_certificatepicker, name='certificatepicker'),
]
