# -*- coding: utf-8 -*-

import datetime

from django.contrib.auth.models import User, Group
from django.contrib.auth.backends import ModelBackend

from userauth.models import *

import re, urllib2, urllib

# Backend per Google OAUTH2
# Es crida sempre amb el keyword "usenamemail", i sempre valida
# No hi ha problema, perquè quan es crida, amb oauth2 ja hem verificat
# que l'usuari és correcte
class DummyBackend:
	def authenticate(self, usernamemail=None):
		try:
			user = User.objects.get(username=usernamemail)
		except User.DoesNotExist:
			user = User.objects.create_user(usernamemail,usernamemail,'')
			user.set_unusable_password()
			user.is_staff = False
			user.is_superuser = False
			user.save()

		return user


	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None


# # Realitzar el ClientLogin de google, a partir d'un user + password
# def checkEmail(email,password):
# 	try:
# 		if not re.match('.*\@esliceu.com',email):
# 			return False
# 		req = urllib2.urlopen('https://www.google.com/accounts/ClientLogin',urllib.urlencode({
# 			'accountType': 'HOSTED',
# 			'Email'      : email,
# 			'Passwd'     : password,
# 			'service'    : 'apps',
# 		}))
# 		return True
# 	except:
# 		return False
#
#
#
# # Backend per ClientLogin, de google. Per mitjans de 2015 ja estarà DEPRECATED
# # Per ara el mantenim per facilitar la vida als usuaris...
# class ClientLoginBackend:
# 	def authenticate(self, username=None, password=None):
# 		if not re.match('.*\@esliceu.com',username):
# 			username = username + '@esliceu.com'
#
# 		if not checkEmail(username,password):
# 			return None
#
# 		try:
# 			user = User.objects.get(username=username)
# 		except User.DoesNotExist:
# 			user = User.objects.create_user(username,username,'')
# 			user.set_unusable_password()
# 			user.is_staff = False
# 			user.is_superuser = False
# 			user.save()
#
# 		return user
#
#
# 	def get_user(self, user_id):
# 		try:
# 			return User.objects.get(pk=user_id)
# 		except User.DoesNotExist:
# 			return None


# Classe per limitar el nombre de logins, per evitar atacs de força bruta contra el servidor
# provant totes les passwords possibles
# TODO: el bloqueig s'hauria de fer per user i IP, no només per usuari...
class RateLimitMixin(object):
	"""
	A mixin to enable rate-limiting in an existing authentication backend.
	"""
	SECONDS = 300  # Màxim 5 failed logins en 5 minuts
	REQUESTS = 5

	def authenticate(self, **kwargs):
		request = kwargs.pop('request', None)
		username = None
		try:
			username = kwargs['username']
		except:
			# No tenim username
			return None

		# TODO: què passa quan fem login amb oauth2? El camp username està buit???? S'haurà de comprovar al servidor...
		if re.match('.*\@esliceu.com',username):
			# Si es tracta d'un login per google (clientLogin), passem
			return None

		try:
			attempts = AuthLog.objects.filter(user=username).order_by('timestamp')
			if len(attempts) > RateLimitMixin.REQUESTS:
				delta = (datetime.datetime.now() - attempts[len(attempts)-RateLimitMixin.REQUESTS].timestamp).seconds
				if delta < RateLimitMixin.SECONDS:
					# Block the user, return None
					# print "BLOCKED:", delta
					return None

		except Exception as e:
			pass

		user = super(RateLimitMixin, self).authenticate(**kwargs)
		if user is None:
			a = AuthLog(user=username, timestamp=datetime.datetime.now())
			a.save()
		else:
			try:
				# Hem aconseguit entrar correctament. Aleshores eliminem de la BBDD
				# els intents fallats.
				attempts = AuthLog.objects.filter(user=username)
				attempts.delete()
			except Exception as e:
				pass


		return user

# Creem una nova classe, que hereda de RateLimitMixin i ModelBackend, que actuarà com a backend
class RateLimitModelBackend(RateLimitMixin, ModelBackend):
	pass
