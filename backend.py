# -*- coding: utf-8 -*-

from django.contrib.auth.models import User, Group

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
