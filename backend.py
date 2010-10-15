# -*- coding: utf-8 -*-

from django.contrib.auth.models import User, Group

import re, urllib2, urllib

# TODO: segur que això va per POST?????
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



class LiceuBackend:
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
