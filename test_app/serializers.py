from rest_framework import serializers
from .models import Test_App

class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test_App
        fields = ('id', 'title', 'description', 'checked')