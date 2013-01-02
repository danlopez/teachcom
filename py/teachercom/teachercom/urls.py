from django.conf.urls import patterns, include, url
from teachercomapp.forms import UserRegistrationForm

from registration.views import register
import registration.backends.default.urls as regUrls
# import registration.backends.simple.urls as simpleUrls

from teachercom import settings
# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

backend_string = ('registration.backends.' + 
    ('default.DefaultBackend' if settings.SEND_EMAIL else 'simple.SimpleBackend'))

register_args = { 'backend': backend_string,'form_class': UserRegistrationForm }

if not settings.SEND_EMAIL:
    register_args['success_url'] = 'send'

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'teachercomapp.views.index', name='index'),
    url(r'^send/', 'teachercomapp.views.send', name='send'),
    url(r'^csv/', 'teachercomapp.views.handle_csv', name='csv'),
    url(r'^call_log/', 'teachercomapp.views.call_log', name='call_log'),
    url(r'^edit_messages/', 'teachercomapp.views.edit_messages', name='edit_messages'),
    url(r'^twilio_calls/(\d+)/$', 'teachercomapp.views.twilio_call', name='twilio_call'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/register/$', register, register_args, name='registration_register'),
    url(r'^accounts/', include(regUrls)),
    url(r'^list_students/','teachercomapp.views.list_students'),
    )
