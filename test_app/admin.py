from django.contrib import admin
from .models import Test_App

class Test_Admin(admin.ModelAdmin):
	list_display = ('title', 'description', 'checked')

# Register your models here.

admin.site.register(Test_App, Test_Admin)
