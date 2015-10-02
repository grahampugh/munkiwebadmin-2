from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', name='logout'),
    url(r'^manifest/', include('manifests.urls'), name='manifests'),
    url(r'^catalog/', include('catalogs.urls'), name='catalogs'),
    url(r'^pkgs/', include('pkgs.urls'), name='pkgs'),
    
    # for compatibility with MunkiReport scripts    
    url(r'^$', include('catalogs.urls'), name='catalogs'),
    (r'', include('tokenapi.urls')),
    )
# comment out the following if you are serving
# static files a different way
urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, }),
    )