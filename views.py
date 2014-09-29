# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson

from django.contrib.auth import logout as log_out
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User, Group

from django.conf import settings

import urllib, urllib2
import random, string, json, re


def logout(request):
	log_out(request)
	return render_to_response(
		'userauth/logout.html', {
	} )

# Panell d'administració de OAUTH2 a google:
# https://console.developers.google.com/project?authuser=0
# Aquesta funció inicia l'autenticació amb google per OAUTH2, substituint l'anterior
# que anava per ClientLogin (obsoleta, ja).
def logingoogle2(request):
	rnd = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
	ses = request.session
	ses['goostate'] = rnd

	next = request.GET.get('next')
	if next != None:
		ses['mynext'] = next
	else:
		ses['mynext'] = None

	ses.save()

	s = 'https://accounts.google.com/o/oauth2/auth?' + urllib.urlencode({
		'redirect_uri': 'https://apps.esliceu.com/auth/oauth2callback',
		'scope': 'email profile',
		'hd': 'esliceu.com',
		'response_type': 'token',
		'state': rnd,
		'client_id': settings.GOOGLECLIENTID,
	})

	return HttpResponseRedirect(s)


# Callback que és cridat per google, un cop l'usuari ha donat permís per usar el seu compte
# Aquest, per javascript cridarà a /auth/gootoken, amb el token com a paràmetre
def oauth2callback(request):
	return render_to_response(
		'userauth/oauth.html', { }
	)

# Rebem el token, i el validem contra google. La resposta ens donarà ja l'email de l'usuari,
# entre d'altres paràmetres. Si hi ha excepció, és que ha fallat
# TODO: amb el wireshark mirar tot el tràfic que va passant. A veure si es pot veure la cookie i tot el demés...
def gootoken(request):
	try:
		access_token = request.GET.get('access_token')
		state = request.GET.get('state')

		# Validem token
		req = urllib2.urlopen('https://www.googleapis.com/oauth2/v1/tokeninfo', urllib.urlencode({'access_token': access_token }))
		dataJson = json.loads(req.read())
		email = dataJson['email']

		# Comprovem variable state
		if state != request.session['goostate']:
			raise Exception("State does not match")

		# Comprovem email acaba en "esliceu.com"
		if None == re.match('.*@esliceu.com$', email):
			raise Exception("Email incorrect")

		# Arribats aquí, podem fer ja el login...
		user = authenticate(usernamemail=email)
		if user is None:
			raise Exception("User auth error")

		# TODO: potser faltaria cridar a "authenticate", amb un dummy backend...
		login(request, user)

		# Finalment, mirem si hi ha pendent la redirecció (next)
		next = None
		try:
			next = request.session['mynext']
		except:
			pass

		if next != None:
			request.session['mynext'] = None
			request.session.save()
			return HttpResponseRedirect(next)
		else:
			return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

	except Exception as e:
		# Alguna cosa ha anat malament. Mostrar missatge d'error i link per tornar-ho a provar
		return HttpResponseRedirect(settings.LOGIN_URL)
