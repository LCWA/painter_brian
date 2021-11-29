from django.db import models

# Create your models here.

class Test_App(models.Model):
	title = models.CharField(max_length = 50)
	description = models.TextField()
	checked = models.BooleanField(default = False)

	def _str_(self):
		return self.title