from django.shortcuts import render
from rest_framework import viewsets
from .serializers import StoreOwnerSerializer, SubCategorySerializer, CategorySerializer
from .models import CustomUser, Category

# Create your views here.
class CreateStoreOwner(viewsets.ModelViewSet):
   """
   API endpoint to signup store owners
   """
   queryset = CustomUser.objects.all()
   serializer_class = StoreOwnerSerializer


class GetCategories(viewsets.ReadOnlyModelViewSet):
   queryset = Category.objects.all()
   serializer_class = CategorySerializer