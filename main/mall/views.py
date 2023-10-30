from rest_framework import viewsets
from .serializers import (StoreOwnerSerializer, SubCategorySerializer, CategorySerializer, 
                           MyTokenObtainPairSerializer, CreateStoreSerializer, ProductSerializer, 
                           ProductImageSerializer, MarketPlaceSerializer,
                           ProductVariantSerializer, StoreProductVariantSerializer)

from .models import CustomUser, Category, Store, Product, ProductImage, MarketPlace, ProductVariant, StoreProductVariant

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
import logging
from django.db.models import Count
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination

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
   queryset = Product.objects.select_related('category', 'subcategory', 'producttype', 'brand').prefetch_related('store', 'images', 'product_variants')
   serializer_class = ProductSerializer
   
   def get_queryset(self):
      category_id = self.request.query_params.get('category')
      
      if category_id is not None:
         category = get_object_or_404(Category, id=category_id)
      else:
         return []
      
      # Get Product
      try:
         product = Product.objects.filter(category=category)
      except Product.DoesNotExist:
         return []
      return product


class ProductVariantView(viewsets.ModelViewSet):
   queryset = ProductVariant.objects.all().prefetch_related('product')
   serializer_class = ProductVariantSerializer

   def get_queryset(self):
      # Assuming you're getting the product ID from the request data
      product_id = self.request.query_params.get('product')

      # Check if the product_id is provided
      if product_id is not None:
         try:
               product_variants = ProductVariant.objects.filter(product=product_id)
               return product_variants
         except ProductVariant.DoesNotExist:
               # Handle the case where no variants are found for the given product
               return ProductVariant.objects.none()
      else:
         # Handle the case where product_id is not provided
         return ProductVariant.objects.none()
      
      
class StoreProductVariantView(viewsets.ModelViewSet):
   queryset = StoreProductVariant.objects.all().select_related('store', 'product_variant')
   serializer_class = StoreProductVariantSerializer
   
   def get_queryset(self):
      store = self.request.query_params.get('store')
      product_id = self.request.query_params.get('product')
      size = self.request.query_params.get('size')

      if product_id is not None:
         product = self.get_product(product_id)
         # Get Product Variants
         product_variants = ProductVariant.objects.filter(product=product, size=size)
      else:
         # If product is not provided, return all product variants
         product_variants = ProductVariant.objects.all()

      if store is not None:
         variants = StoreProductVariant.objects.filter(product_variant__in=product_variants, store=store)
         return product_variants, variants

      # If store is not provided, return all variants
      return product_variants, None

   def list(self, request, *args, **kwargs):
      product_variants, store_variants = self.get_queryset()

      # Handle the case where no product variants are found
      if not product_variants.exists():
         return Response({"message": "No product variants found."})

      # Serialize data using your serializer
      product_variants_serializer = ProductVariantSerializer(product_variants, many=True)
      serialized_product_variants = product_variants_serializer.data

      # Serialize store_variants using a custom serialization method
      serialized_store_variants = self.serialize_store_product_variants(store_variants)

      response_data = {
         "product_variant": serialized_product_variants,
         "store_variant": serialized_store_variants
      }

      return Response(response_data)

   def serialize_store_product_variants(self, store_variants):
      serialized_data = []
      for store_variant in store_variants:
         serialized_store_variant = {
               "id": store_variant.id,
               "retail_price": store_variant.retail_price,
               "store": str(store_variant.store.id),  # Convert UUID to string if needed
               "product_variant": store_variant.product_variant.id,
               "size": store_variant.product_variant.size if store_variant.product_variant.size else None,
         }
         serialized_data.append(serialized_store_variant)
      return serialized_data

   def get_product(self, product_id):
      return get_object_or_404(Product, id=product_id)

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
   
class MarketPlacePagination(PageNumberPagination):
   page_size = 5


class MarketPlaceView(viewsets.ModelViewSet):
   serializer_class = MarketPlaceSerializer
   pagination_class = MarketPlacePagination

   def get_queryset(self):
      store_id = self.request.query_params.get("store")
      
      try:
         store = get_object_or_404(Store, id=store_id)
         # Filter the queryset based on the specified store and list_product=True
         queryset = MarketPlace.objects.filter(store=store, list_product=True).select_related('product').order_by("-id")
         # cache.set(cache_key, queryset, timeout=100)
         return queryset
      except Store.DoesNotExist:
         return MarketPlace.objects.none()
      

class DropshipperDashboardCounts(APIView):
   def get(self, request):
      # Get Store
      store_id = request.query_params.get('store')
      store = self.get_store(store_id)
      
      # Get Number of Listed Products
      try:
         product_count = MarketPlace.objects.filter(store=store, list_product=True).aggregate(product_count=Count('id'))['product_count']
      except MarketPlace.DoesNotExist:
         return MarketPlace.objects.none
      
      data = {
         "No. of Listed Products": product_count
      }
      
      return Response(data, status=status.HTTP_200_OK)

   
   def get_store(self, store_id):
      return get_object_or_404(Store, id=store_id)
