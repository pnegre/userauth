# -*- coding: utf-8 -*-

from django.contrib.auth.models import User, Group
from django.contrib.auth.backends import ModelBackend

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


# Realitzar el ClientLogin de google, a partir d'un user + password
def checkEmail(email,password):
	try:
		if not re.match('.*\@esliceu.com',email):
			return False
		req = urllib2.urlopen('https://www.google.com/accounts/ClientLogin',urllib.urlencode({
			'accountType': 'HOSTED',
			'Email'      : email,
			'Passwd'     : password,
			'service'    : 'apps',
		}))
		return True
	except:
		return False



# Backend per ClientLogin, de google. Per mitjans de 2015 ja estarà DEPRECATED
# Per ara el mantenim per facilitar la vida als usuaris...
class ClientLoginBackend:
	def authenticate(self, username=None, password=None):
		if not re.match('.*\@esliceu.com',username):
			username = username + '@esliceu.com'

		if not checkEmail(username,password):
			return None

		try:
			user = User.objects.get(username=username)
		except User.DoesNotExist:
			user = User.objects.create_user(username,username,'')
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


class RateLimitMixin(object):
	"""
	A mixin to enable rate-limiting in an existing authentication backend.
	"""
	cache_prefix = 'ratelimitbackend-'
	minutes = 5
	requests = 30
	username_key = 'username'

	def authenticate(self, **kwargs):
		print kwargs
		request = kwargs.pop('request', None)
		username = kwargs[self.username_key]
		print username
		user = super(RateLimitMixin, self).authenticate(**kwargs)
		if user is None:
			print "Fallo:", username
		else:
			print "Success:", username

		return user
		# if request is not None:
		#     counts = self.get_counters(request)
		#     if sum(counts.values()) >= self.requests:
		#         logger.warning(
		#             u"Login rate-limit reached: username '{0}', IP {1}".format(
		#                 username, self.get_ip(request),
		#             )
		#         )
		#         raise RateLimitException('Rate-limit reached', counts)
		# else:
		#     warnings.warn(u"No request passed to the backend, unable to "
		#                   u"rate-limit. Username was '%s'" % username,
		#                   stacklevel=2)

		# print user, request
		# if user is None and request is not None:
		# 	print "Fallo:", username, self.get_ip(request)

			#     logger.info(
			#         u"Login failed: username '{0}', IP {1}".format(
			#             username,
			#             self.get_ip(request),
			#         )
			#     )
			#     cache_key = self.get_cache_key(request)
			#     self.cache_incr(cache_key)
		return user

class RateLimitModelBackend(RateLimitMixin, ModelBackend):
	pass
