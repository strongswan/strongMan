from django.conf.urls import url

from . import views

app_name = 'certificates'
urlpatterns = [
    url(r'add$', views.add, name='add'),
    #url(r'(?P<pk>\d+)/$', views.ConfigurationUpdate.as_view(), name='configuration_update'),
    #url(r'config$', views.ConfigurationUpdate.as_view(), name='create_config'),
]
