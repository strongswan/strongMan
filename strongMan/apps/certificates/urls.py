from django.conf.urls import url

from . import views

app_name = 'connections'
urlpatterns = [
    url(r'create$', views.ConfigurationCreate.as_view(), name='configuration_add'),
    url(r'(?P<pk>\d+)/$', views.ConfigurationUpdate.as_view(), name='configuration_update'),
    url(r'config$', views.ConfigurationUpdate.as_view(), name='create_config'),
]
