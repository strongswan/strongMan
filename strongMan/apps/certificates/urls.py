from django.conf.urls import url

from . import views

app_name = 'certificates'
urlpatterns = [
    url(r'add$', views.add, name='add'),
    url(r'overview_ca$', views.overview_ca, name='overview_ca'),
    url(r'overview_cert$', views.overview_certs, name='overview_certs'),
    url(r'$', views.overview, name='overview'),

    #url(r'(?P<pk>\d+)/$', views.ConfigurationUpdate.as_view(), name='configuration_update'),
    #url(r'config$', views.ConfigurationUpdate.as_view(), name='create_config'),
]
