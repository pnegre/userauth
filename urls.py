# -*- coding: utf-8 -*-

from django.conf.urls import patterns

urlpatterns = patterns('',

	(r'^login/$', 'userauth.views.mylogin'),
	(r'^login2/$', 'userauth.views.mylogin2'),
	(r'^logout/$', 'userauth.views.logout'),
	# (r'^error/$', 'userauth.views.loginError'),

	(r'^logingoogle2/$', 'userauth.views.logingoogle2'),
	(r'^oauth2callback/$', 'userauth.views.oauth2callback'),

)
