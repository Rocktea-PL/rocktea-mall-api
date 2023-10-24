from rest_framework import viewsets

from .serializers import (StoreOwnerSerializer, SubCategorySerializer, CategorySerializer, 
                           MyTokenObtainPairSerializer, CreateStoreSerializer, ProductSerializer, 
                           PriceSerializer, SizeSerializer, ProductImageSerializer, MarketPlaceSerializer)

from .models import CustomUser, Category, Store, Product, Size, Price, ProductImage, MarketPlace
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import serializers
from helpers.views import BaseView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.db import transaction
from rest_framework.generics import ListCreateAPIView
from .task import upload_image
from rest_framework.parsers import MultiPartParser
from django.shortcuts import get_object_or_404

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
   queryset = Product.objects.select_related('category', 'subcategory', 'producttype', 'brand').prefetch_related('sizes', 'images', 'store')
   serializer_class = ProductSerializer


class SizeViewSet(viewsets.ModelViewSet):
   queryset = Size.objects.all()
   serializer_class = SizeSerializer


class PriceViewSet(viewsets.ModelViewSet):
   # queryset = Price.objects.all()
   serializer_class = PriceSerializer
   
   def get_queryset(self):
      product_id = self.kwargs.get('sn')
      if product_id:
         return Price.objects.filter(product__sn=product_id)
      else:
         return Price.objects.all()


class GetCategories(viewsets.ReadOnlyModelViewSet):
   queryset = Category.objects.all()
   serializer_class = CategorySerializer #TODO Differ this based on user


class UploadProductImage(ListCreateAPIView):
   # PENDING ERROR (BKLOG-#001): PERMISSIONS NOT WORKING and FILE SIZE VALIDATION NOT INCLUDED
   
   queryset = ProductImage.objects.all()
   serializer_class = ProductImageSerializer
   parser_classes = (MultiPartParser,)
   
   def perform_create(self, serializer):
      image = self.request.FILES.get('image')
      images = serializer.save()

      if image:
         # Start the Celery task to upload the large video to Cloudinary
         result = upload_image.delay(images.id, image.read(), image.name, image.content_type)
         task_id = result.id
         task_status = result.status

         if task_status == "SUCCESS":
               return Response({'message': 'Course created successfully.'}, status=status.HTTP_201_CREATED)
         elif task_status in ("FAILURE", "REVOKED"):
               images.delete()
               return Response({'message': 'Failed to upload video.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
         else:
               return Response({'message': 'Video upload task is in progress.'}, status=status.HTTP_202_ACCEPTED)

      return Response({'message': 'Image created successfully.'}, status=status.HTTP_201_CREATED)
   
   
class MarketPlaceView(viewsets.ModelViewSet):
   serializer_class = MarketPlaceSerializer

   def get_queryset(self):
      store_id = self.request.query_params.get("store")

      try:
         store = get_object_or_404(Store, id=store_id)
         # Filter the queryset based on the specified store and list_product=True
         queryset = MarketPlace.objects.filter(store=store, list_product=True).select_related('product')

         return queryset
      except Store.DoesNotExist:
         return MarketPlace.objects.none()