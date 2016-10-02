# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect

from django.contrib.auth import logout as log_out
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import login as genericLogin
from django.conf import settings

import httplib2
import json, re

from oauth2client import client

from ratelimit.decorators import ratelimit

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

#
# OAUTH2, primer pas
#
def logingoogle2(request):
	ses = request.session
	next = request.GET.get('next')
	if next != None:
		ses['mynext'] = next
	else:
		ses['mynext'] = None

	flow = client.OAuth2WebServerFlow(
		client_id=settings.GOOGLECLIENTID,
		client_secret=settings.GOOGLESECRET,
		scope="email profile",
		redirect_uri=settings.GOOGLEREDIRECT
	)

	ses['flow'] = flow
	ses.save()

	auth_uri = flow.step1_get_authorize_url()
	return HttpResponseRedirect(auth_uri)


#
# Torna un array amb la informació bàsica de l'usuari:
# nom, llinatge i email
#
def getUserInfo(credentials):
	http = httplib2.Http()
	credentials.authorize(http)
	resp, cont = http.request(URI_GOOGLE_PROFILE)
	respJson = json.loads(cont)
	return [ respJson['email'], respJson['given_name'], respJson['family_name'] ]


#
# Segon pas de autenticació OAUTH2
# S'obté la informació del profile de l'usuari
#
def oauth2callback(request):
	try:
		code = request.GET.get('code')
		flow = request.session['flow']
		credentials = flow.step2_exchange(code)
		email, given_name, family_name = getUserInfo(credentials)

		# Comprovem que el email és del liceu
		if None == re.match('.*@esliceu.com$', email):
			raise Exception("Només són vàlides les credencials @esliceu")

		# Arribats aquí, podem fer ja el login...
		# Autentiquem amb DummyBackend (per les keywords que passem a authenticate)
		user = authenticate(usernamemail=email, realusername=[ given_name, family_name ])
		if user is None:
			raise Exception("User auth error")

		# Comprovem que l'usuari està marcat com a actiu
		if not user.is_active:
			raise Exception("User not active")

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
		#return HttpResponse("ERROR" + str(e))
		return render_to_response('userauth/error.html', { 'message': str(e)})
		# return HttpResponseRedirect(settings.LOGIN_URL)

# 
# def loginError(request):
# 	return render_to_response('userauth/error.html', { 'message': "hey"})
