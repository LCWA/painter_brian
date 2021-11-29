from django.shortcuts import render
from rest_framework import viewsets
from .serializers import TestSerializer
from .models import Test_App

# Create your views here.

class TestView(viewsets.ModelViewSet):
    serializer_class = TestSerializer
    queryset = Test_App.objects.all()