# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils import simplejson

from django.contrib.auth import logout as log_out


def logout(request):
	log_out(request)
	return render_to_response(
		'userauth/logout.html', { 
	} )

