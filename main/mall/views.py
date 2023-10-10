from rest_framework import viewsets

from .serializers import (StoreOwnerSerializer, SubCategorySerializer, CategorySerializer, 
                           MyTokenObtainPairSerializer, CreateStoreSerializer, ProductSerializer, 
                           PriceSerializer, SizeSerializer)

from .models import CustomUser, Category, Store, Product, Size, Price
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import serializers
from helpers.views import BaseView
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.
class CreateStoreOwner(viewsets.ModelViewSet):
   """
   Sign Up Store Owners Feature
   """
   queryset = CustomUser.objects.all()
   serializer_class = StoreOwnerSerializer
   renderer_classes= [JSONRenderer]


class CreateStore(viewsets.ModelViewSet):
   """
   Create Store Feature 
   """
   queryset = Store.objects.all()
   serializer_class = CreateStoreSerializer
   
   def get_serializer_context(self):
      return {'request': self.request}
      
   def perform_update(self, serializer):
      # You can override this method to add custom logic when updating the instance
      serializer.save()
 

# Sign In Store User
class SignInUserView(TokenObtainPairView):
   permission_classes = (permissions.AllowAny,)
   serializer_class = MyTokenObtainPairSerializer
   

class ProductViewSet(viewsets.ModelViewSet):
   queryset = Product.objects.all()
   serializer_class = ProductSerializer


class SizeViewSet(viewsets.ModelViewSet):
   queryset = Size.objects.all()
   serializer_class = SizeSerializer


class PriceViewSet(viewsets.ModelViewSet):
   queryset = Price.objects.all()
   serializer_class = PriceSerializer


class GetCategories(viewsets.ReadOnlyModelViewSet):
   queryset = Category.objects.all()
   serializer_class = CategorySerializer #TODO Differ this based on user