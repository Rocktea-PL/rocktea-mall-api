from django.shortcuts import render
from rest_framework import viewsets
from .serializers import StoreOwnerSerializer
from .models import CustomUser

# Create your views here.
class CreateStoreOwner(viewsets.ModelViewSet):
   """
   API endpoint to signup store owners
   """
   queryset = CustomUser.objects.all()
   serializer_class = StoreOwnerSerializer

