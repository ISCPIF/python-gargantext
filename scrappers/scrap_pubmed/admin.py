from django.contrib import admin
from gargantext_web.settings import STATIC_ROOT
# Register your models here.
import os
import datetime

class Logger():
	
	def write(msg):
		path = "Logs/"
		Logger.ensure_dir(path)
		
		nowfull = datetime.datetime.now().isoformat().split("T")
		date = nowfull[0]
		time = nowfull[1]

		return path

	def ensure_dir(f):
		d = os.path.dirname(f)
		if not os.path.exists(d):
			os.makedirs(d)
