from django.conf.urls import re_path

from . import views

app_name = 'certificates'
urlpatterns = [
    re_path(r'add$', views.add, name='add'),
    re_path(r'add_form$', views.add_form, name='add_form'),
    re_path(r'^(?P<certificate_id>[0-9]+)$', views.details, name='details'),
    re_path(r'overview_ca$', views.overview_ca, name='overview_ca'),
    re_path(r'overview_cert$', views.overview_certs, name='overview_certs'),
    re_path(r'overview_vici$', views.overview_vici, name='overview_vici'),
    re_path(r'$', views.overview, name='overview'),
]
