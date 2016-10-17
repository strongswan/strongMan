from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from .apps import views
from .apps.certificates import urls as certificates_url
from .apps.connections import urls as connections_urls
from .apps.server_overview import urls as prold_urls
from .apps.views import index

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^connections/', include(connections_urls)),
    url(r'^certificates/', include(certificates_url)),
    url(r'^login/?$', views.login, name='login'),
    url(r'^logout/?$', views.logout, name='logout'),
    url(r'change_pw$', views.pw_change, name='pw_change'),
    url(r'^about/?$', views.about, name='about'),
    url(r'^server_overview/', include(prold_urls)),
]

handler400 = 'strongMan.apps.views.bad_request'
handler403 = 'strongMan.apps.views.permission_denied'
handler404 = 'strongMan.apps.views.page_not_found'
handler500 = 'strongMan.apps.views.server_error'

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
