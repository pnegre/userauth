# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import *

class AuthLog(models.Model):
    user = models.CharField(max_length=100)
    timestamp = models.DateTimeField()

    def __unicode__(self):
        return self.user + " " + str(self.timestamp)
