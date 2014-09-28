# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('',

	(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'userauth/login.html'}),
	(r'^loginexpert/$', 'django.contrib.auth.views.login', {'template_name': 'userauth/login2.html'}),
	(r'^logout/$', 'userauth.views.logout'),

	(r'^logingoogle2/$', 'userauth.views.logingoogle2'),
	(r'^oauth2callback/$', 'userauth.views.oauth2callback'),
	(r'^gootoken/$', 'userauth.views.gootoken'),

)
