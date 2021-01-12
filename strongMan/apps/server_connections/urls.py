from django.conf.urls import re_path

from . import views

app_name = 'server_connections'
urlpatterns = [
    re_path(r'^$', views.overview, name='index'),
    re_path(r'^add/(?P<connection_type>\w+)/$', views.create, name='choose'),
    re_path(r'^(?P<id>\d+)/$', views.update, name='update'),
    re_path(r'delete/(?P<id>\d+)/$', views.delete_connection, name='delete'),
    re_path(r'terminate_sa/$', views.terminate_sa, name='terminate'),
    re_path(r'state/(?P<id>\d+)/$', views.get_state, name='state'),
    re_path(r'log/$', views.get_log, name='log'),
    re_path(r'toggle/$', views.toggle_connection, name='toggle'),
    re_path(r'info/$', views.get_sa_info, name='info'),
    re_path(r'poolpicker/$', views.get_poolpicker, name='poolpicker'),
    re_path(r'certificatepicker/$', views.get_certificatepicker, name='certificatepicker'),
    re_path(r'capicker/$', views.get_capicker, name='capicker'),
]
