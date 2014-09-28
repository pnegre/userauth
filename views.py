# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson

from django.contrib.auth import logout as log_out

from django.conf import settings

import urllib, urllib2
import json


def logout(request):
	log_out(request)
	return render_to_response(
		'userauth/logout.html', {
	} )

def logingoogle2(request):
	print request.session.session_key

	s = 'https://accounts.google.com/o/oauth2/auth?' + 'scope=email%20profile&' + \
		'redirect_uri=http%3A%2F%2Fappsproves.esliceu.com:8000%2Fauth%2Foauth2callback&' + \
		'hd=esliceu.com&' + \
		'response_type=token&' + \
		'state=abc123&' + \
		'client_id=' + settings.GOOGLECLIENTID

	return HttpResponseRedirect(s)


# Callback que és cridat per google, un cop l'usuari ha donat permís per usar el seu compte
# Aquest, per javascript cridarà a /auth/gootoken, amb el token com a paràmetre
def oauth2callback(request):
	return render_to_response(
		'userauth/oauth.html', { }
	)


# Rebem el token, i el validem contra google. La resposta ens donarà ja l'email de l'usuari,
# entre d'altres paràmetres. Si hi ha excepció, és que ha fallat
# TODO: Aquí veig un problema: si algú té accés a aquest "token", podrà entrar tranquil·lament suplantant l'identitat de l'usuari...
def gootoken(request):
	access_token = request.GET.get('access_token')

	# Validem token
	req = urllib2.urlopen('https://www.googleapis.com/oauth2/v1/tokeninfo', urllib.urlencode({'access_token': access_token }))
	dataJson = json.loads(req.read())
	email = dataJson['email']

	print "EMAIL: ", email
	print dataJson
