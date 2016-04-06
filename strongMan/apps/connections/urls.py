from django.conf.urls import url

from . import views

app_name = 'connections'
urlpatterns = [
    url(r'^$', views.ChooseTypView.as_view(), name='connections_choose'),
    url(r'^create/$', views.create, name='connection_create'),
    url(r'^(?P<id>\d+)/$', views.update, name='connection_create_eap'),
    url(r'delete/(?P<id>\d+)/$', views.delete_connection, name='connection_delete'),
    url(r'toggle/$', views.toggle_connection, name='connection_toggle'),
]
