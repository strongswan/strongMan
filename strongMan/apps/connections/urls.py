from django.conf.urls import url

from . import views

app_name = 'connections'
urlpatterns = [
    url(r'create$', views.ConnectionCreateView.as_view(), name='connection_create'),
    url(r'(?P<pk>\d+)/$', views.ConnectionUpdateView.as_view(), name='connection_update'),
]
