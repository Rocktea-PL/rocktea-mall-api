from django.shortcuts import render
from rest_framework import viewsets
from .serializers import StoreOwnerSerializer, SubCategorySerializer, CategorySerializer, SignInUser
from .models import CustomUser, Category
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions


# Create your views here.
class CreateStoreOwner(viewsets.ModelViewSet):
   """
   API endpoint to signup store owners
   """
   queryset = CustomUser.objects.all()
   serializer_class = StoreOwnerSerializer


# Sign In Users
class SignInUserView(TokenObtainPairView):
   permission_classes = (permissions.AllowAny,)
   serializer_class = SignInUser


class GetCategories(viewsets.ReadOnlyModelViewSet):
   queryset = Category.objects.all()
   serializer_class = CategorySerializer
   
