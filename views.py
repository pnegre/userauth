# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect

from django.contrib.auth import logout as log_out
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import login as genericLogin
from django.conf import settings

import urllib, urllib2
import random, string, json, re

from ratelimit.decorators import ratelimit

URI_GOOGLE_OAUTH1 =       'https://accounts.google.com/o/oauth2/auth'
URI_GOOGLE_OBTAIN_TOKEN = 'https://accounts.google.com/o/oauth2/token'
URI_GOOGLE_TOKENINFO =    'https://www.googleapis.com/oauth2/v1/tokeninfo'
URI_GOOGLE_PROFILE =      'https://www.googleapis.com/oauth2/v1/userinfo'

# Pantalla de login on es pot triar si entrem amb google o mitjançant
# un usuari de la base de dades local (modelbackend)
def mylogin(request):
	return genericLogin(request, template_name='userauth/login.html')

# La vista del login per usuari (modelbackend) la limitem mitjançant
# el mòdul "ratelimit": https://github.com/jsocol/django-ratelimit
@ratelimit(key='ip', rate='5/2m', block=True)
def mylogin2(request):
	return genericLogin(request, template_name='userauth/login2.html')

def logout(request):
	if request.method == 'POST':
		log_out(request)
		return render_to_response('userauth/logout.html')

# Vista per mostrar la pantalla de "superat el número d'intents màxims"
def blockedWarning(request, exception):
	return render_to_response('userauth/blocked.html')

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

	s = URI_GOOGLE_OAUTH1 + '?' + urllib.urlencode({
		'redirect_uri': settings.GOOGLEREDIRECT,
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
		req = urllib2.urlopen(URI_GOOGLE_OBTAIN_TOKEN, urllib.urlencode({
			'code': code,
			'client_id': settings.GOOGLECLIENTID,
			'client_secret': settings.GOOGLESECRET,
			'grant_type': 'authorization_code',
			'redirect_uri': settings.GOOGLEREDIRECT,
		}))

		respJson = json.loads(req.read())
		access_token = respJson['access_token']

		# Validem token
		req = urllib2.urlopen(URI_GOOGLE_TOKENINFO, urllib.urlencode({
			'access_token': access_token
		}))
		dataJson = json.loads(req.read())
		email = dataJson['email']

		userRealName = ["Unknown", "Unknown"]
		try:
			req = urllib2.urlopen(URI_GOOGLE_PROFILE + "?" + urllib.urlencode({
				'alt': 'json',
				'access_token': access_token,
				'userId': 'me',
			}))
			djson2 = json.loads(req.read())
			print "---- DATA2:", djson2
			userRealName = [ djson2['given_name'], djson2['family_name'] ]
		except Exception as e:
			pass

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
		user = authenticate(usernamemail=email, realusername=userRealName)
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
