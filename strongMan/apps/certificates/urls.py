from django.conf.urls import url

from . import views

app_name = 'certificates'
urlpatterns = [
    url(r'add$', views.add, name='add'),
    url(r'^(?P<certificate_id>[0-9]+)$', views.details, name='details'),
    url(r'overview_ca$', views.overview_ca, name='overview_ca'),
    url(r'overview_cert$', views.overview_certs, name='overview_certs'),
    url(r'$', views.overview, name='overview'),
]
