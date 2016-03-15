from django.conf.urls import url

from . import views
app_name='vici'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^addcon/', views.add_conn, name='addcon'),
    url(r'^cert/', views.certificate, name='cert'),
    url(r'^certequal/', views.cert_upload, name='certupload'),

]
