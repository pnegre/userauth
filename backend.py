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
	def authenticate(self, usernamemail=None, realusername=None):
		try:
			user = User.objects.get(username=usernamemail)
		except User.DoesNotExist:
			user = User.objects.create_user(usernamemail,usernamemail,'')
			user.set_unusable_password()
			user.is_staff = False
			user.is_superuser = False
			user.first_name = realusername[0]
			user.last_name = realusername[1]
			user.save()

		return user


	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None
