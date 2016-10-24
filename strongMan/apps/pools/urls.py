from django.conf.urls import url

from . import views

app_name = 'pools'
urlpatterns = [
    url(r'^$', views.overview, name='index'),
    url(r'add$', views.add, name='add'),
    ]