from django.conf.urls import url

from . import views

app_name = 'connections'
urlpatterns = [
    url(r'^$', views.overview, name='index'),
    url(r'^add/$', views.create, name='connections_choose'),
    url(r'^add/create/$', views.create, name='connection_create'),
    url(r'^(?P<id>\d+)/$', views.update, name='connection_update'),
    url(r'delete/(?P<id>\d+)/$', views.delete_connection, name='connection_delete'),
    url(r'toggle/$', views.toggle_connection, name='connection_toggle'),
]
