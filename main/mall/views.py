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
   
   # def get_queryset(self):
   #    category_id = self.request.query_params.get('category')
      
   #    if category_id is not None:
   #       category = get_object_or_404(Category, id=category_id)
   #    else:
   #       return []
      
      # Get Product
      # product = Product.objects.filter()


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


class ProductPrice(APIView):
   def post(self, request, *args, **kwargs):
      # Add Profit Price
      data = request.data
      
      store = data.get('store')
      verified_store = self.get_store(store)
      
      product = data.get('product')
      verified_product = self.get_product(product)
      
      product_size = data.get('size')
      verified_size = self.get_size(product_size)

      # Convert product_size to integer if it's a string
      product_size = int(verified_size.id) if isinstance(verified_size.id, str) else verified_size.id

      if product_size not in self.get_product_sizes(verified_product):
         return Response({"error": f"This Product does not have the size {product_size}", "ids": self.get_product_sizes(verified_product)}, status=status.HTTP_404_NOT_FOUND)

      profit = data.get('profit_price')

      # Create StoreProfit
      try:
         storeprofit = StoreProfit.objects.create(store=verified_store, product=verified_product, size=verified_size, profit_price=profit)
         return Response({"message": "Profit created successfully"}, status=status.HTTP_201_CREATED)
      except Exception as e:
         logging.exception("An Error Unexpectedly Occurred")
         return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      
      profit = data.get('profit_price')
      
      # Create Profit
      try:
         storeprofit = StoreProfit.objects.create(store=verified_store, product=verified_product, size=product_size, profit_price=profit)
         return Response({"message": "Profit created successfully"}, status=status.HTTP_201_CREATED)
      except Exception as e:
         logging.exception("An Error Unexpectedly Occurred")
         return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   def get(self, request, *args, **kwargs):
      # Collect Data
      data = request.data
      
      # Verify Product
      product_id = data.get('product')
      verified_product = self.get_product(product_id)
      
      # Get Product Size
      psize = self.get_product_sizes(verified_product)
      
      # Product Price
      product_prices = self.get_product_prices(verified_product)

      return Response({"Prices": product_prices}, status=status.HTTP_200_OK)

   def get_product(self, product_id):
      return get_object_or_404(Product, id=product_id)
   
   def get_store(self, store_id):
      return get_object_or_404(Store, id=store_id)
   
   def get_size(self, size_id):
      return get_object_or_404(Size, id=size_id)

   def get_product_prices(self, product):
      prices = Price.objects.filter(product=product)

      if prices.exists():
         # Serialize the prices if needed
         serialized_prices = [{f"{price.id}": price.price} for price in prices]
         return serialized_prices
      else:
         return None

   def get_product_sizes(self, product):
      try:
         product = Product.objects.get(id=product).product_price.all()
      except Product.DoesNotExist:
         return Response({"message": f"Product ID {product} not found"}, status=status.HTTP_400_BAD_REQUEST)
      
      # print([price.size.id for price in product])
      return [price.size.id for price in product]