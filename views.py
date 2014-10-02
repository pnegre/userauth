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
		'redirect_uri': 'http://appsproves.esliceu.com:8000/auth/oauth2callback',
		'scope': 'email profile',
		'hd': 'esliceu.com',
		'response_type': 'code',
		'state': rnd,
		'client_id': settings.GOOGLECLIENTID,
	})

	return HttpResponseRedirect(s)


# Google cridarà a /auth/oauth2callback i per GET enviarà el "code",
# que serveix per obtenir el token (combinant-ho amb el SECRET de la consola de google).
# També comprovarem "state", generat aleatòriament abans.
def oauth2callback(request):
	try:
		state = request.GET.get('state')
		code = request.GET.get('code')

		# Comprovem variable state
		if state != request.session['goostate']:
			raise Exception("State does not match")

		# Obtenim el token a partir del "code"
		req = urllib2.urlopen('https://accounts.google.com/o/oauth2/token', urllib.urlencode({
			'code': code,
			'client_id': settings.GOOGLECLIENTID,
			'client_secret': settings.GOOGLESECRET,
			'grant_type': 'authorization_code',
			'redirect_uri': 'http://appsproves.esliceu.com:8000/auth/oauth2callback',
		}))
		respJson = json.loads(req.read())
		access_token = respJson['access_token']

		# Validem token
		req = urllib2.urlopen('https://www.googleapis.com/oauth2/v1/tokeninfo', urllib.urlencode({'access_token': access_token }))
		dataJson = json.loads(req.read())
		email = dataJson['email']

		# Comprovem el clientID
		if dataJson['audience'] != settings.GOOGLECLIENTID:
			raise Exception("Client ID error")

		# Comprovem variable state
		if state != request.session['goostate']:
			raise Exception("State does not match")

		# Comprovem email acaba en "esliceu.com"
		if None == re.match('.*@esliceu.com$', email):
			raise Exception("Email incorrect")

		# Arribats aquí, podem fer ja el login...
		# Autentiquem amb DummyBackend (per les keywords que passem a authenticate)
		user = authenticate(usernamemail=email)
		if user is None:
			raise Exception("User auth error")

		# Es fa el login per django, un cop el backend ens ha autenticat
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
		# return HttpResponse("ERROR" + str(e))
		return HttpResponseRedirect(settings.LOGIN_URL)
