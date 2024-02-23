# from rest_framework import viewsets
from .serializers import (
   StoreOwnerSerializer, 
   SubCategorySerializer, 
   CategorySerializer, 
   MyTokenObtainPairSerializer, 
   CreateStoreSerializer, 
   ProductSerializer, 
   ProductImageSerializer,
   MarketPlaceSerializer, 
   ProductVariantSerializer, 
   ProductDetailSerializer, 
   BrandSerializer, 
   ProductTypesSerializer, 
   WalletSerializer, 
   StoreProductPricingSerializer, 
   ServicesBusinessInformationSerializer, 
   LogisticSerializer,
   OperationsSerializer
)

from .models import (
   CustomUser, 
   Category, 
   Store, 
   Product, 
   ProductImage, 
   MarketPlace, 
   ProductVariant, 
   Brand, 
   ProductTypes, 
   SubCategories, 
   Wallet, 
   ServicesBusinessInformation, 
   StoreProductPricing,
   Wallet
)

from order.models import StoreOrder
from order.serializers import OrderSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions, viewsets, status, serializers
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.decorators import action
from helpers.views import BaseView
from django.db import transaction
from .task import upload_image
from django.db.models import Count
from django.core.cache import cache
import logging
from .store_features.get_store_id import get_store_instance

# Create your views here.
class CreateStoreOwner(viewsets.ModelViewSet):
   """
   Sign Up Store Owners Feature
   """
   queryset = CustomUser.objects.select_related('associated_domain')
   serializer_class = StoreOwnerSerializer
   renderer_classes= [JSONRenderer]
   # http_method_names = ['post', 'patch']
   
   def get_queryset(self):
      # Get the user_id from cookies
      user_id = self.request.query_params.get('mallcli')

      # If user_id is present in cookies, filter the queryset by it
      if user_id:
            queryset = CustomUser.objects.filter(id=user_id)
      else:
         # If user_id is not present, return an empty queryset or handle it as per your requirement
         queryset = CustomUser.objects.none()
      return queryset


class CreateLogisticsAccount(viewsets.ModelViewSet):
   queryset = CustomUser.objects.filter(is_logistics=True)
   serializer_class = LogisticSerializer


class CreateOperationsAccount(viewsets.ModelViewSet):
   queryset = CustomUser.objects.filter(is_operations=True)
   serializer_class = OperationsSerializer


class CreateStore(viewsets.ModelViewSet):
   # queryset = Store.objects.all()  # You can uncomment this if you want to retrieve all stores

   serializer_class = CreateStoreSerializer

   def get_queryset(self):
      # Extracting the domain name from the request
      # if user is None or user.is_store_owner is False:
      domain = self.request.META.get("HTTP_ORIGIN", None)
      # Filter stores based on domain_name
      queryset = Store.objects.filter(domain_name=domain)
      return queryset
   
   def get_serializer_context(self):
      return {'request': self.request}


class GetStoreDropshippers(viewsets.ModelViewSet):
   queryset = Store.objects.all() 
   serializer_class = CreateStoreSerializer
   
   
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


class CreateAndGetStoreProductPricing(APIView):
   def post(self, request):
      collect = request.data
      store_id = request.domain_name  
      product_id = collect.get("product")
      retail_price = collect.get("retail_price")

      # Fetch the store and product objects
      store = get_object_or_404(Store, id=store_id)
      product = Product.objects.get(pk=product_id)

      # Check if the product pricing is valid before proceeding
      self.validate_product_pricing(store, product)

      # Create the StoreProductPricing instance
      store_product_price = StoreProductPricing.objects.create(
         store=store,
         product=product,
         retail_price=retail_price
      )
      store_product_price.save()  # Call the save method

      serializer = StoreProductPricingSerializer(store_product_price)
      return Response({"message": "Product pricing validated successfully.", "data": serializer.data})

   def validate_product_pricing(self, store, product):
      existing_pricing = StoreProductPricing.objects.filter(store=store, product=product).exclude(id=None).first()
      if existing_pricing:
         raise serializers.ValidationError("Pricing for this product in this store already exists.")

   def get(self, request):
      # Retrieve all StoreProductPricing instances
      store_product_prices = StoreProductPricing.objects.all()
      serializer = StoreProductPricingSerializer(store_product_prices,many=True)
      return Response(serializer.data, status=status.HTTP_200_OK)



class StoreProductPricingAPIView(APIView):
   def get(self, request):
      # store_id = request.query_params.get("store")
      try:
         # Retrieve all store prices related to the specified store
         store_prices = StoreProductPricing.objects.filter(
               store_id=get_store_instance(request))
         
         # Serialize the data
         store_prices_serializer = StoreProductPricingSerializer(
               store_prices, many=True)

         # Return the serialized data as the API response
         return Response(store_prices_serializer.data, status=status.HTTP_200_OK)

      except Exception as e:
         # Handle exceptions, you might want to log the error or return a different response
         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   

   def delete(self, request, store_id):
      try:
         # Get the store price to be deleted
         store_price = StoreProductPricing.objects.get(store_id=store_id, id=get_store_instance())

         # Delete the store price
         store_price.delete()

         # Return a success response
         return Response({'detail': 'Store price deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

      except StoreProductPricing.DoesNotExist:
         # Return a 404 response if the store price is not found
         return Response({'detail': 'Store price not found.'}, status=status.HTTP_404_NOT_FOUND)

      except Exception as e:
         # Handle other exceptions, you might want to log the error or return a different response
         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetCategories(viewsets.ReadOnlyModelViewSet):
   queryset = Category.objects.all()
   serializer_class = CategorySerializer
   
   def retrieve(self, request, *args, **kwargs):
      instance = self.get_object()
      category_serializer = self.get_serializer(instance)
      subcategories_serializer = SubCategorySerializer(instance.subcategories.all(), many=True)
      product_types_serializer = ProductTypesSerializer(ProductTypes.objects.filter(subcategory__in=instance.subcategories.all()), many=True)

      return Response({
         'category': category_serializer.data,
         'subcategories': subcategories_serializer.data,
         'product_types': product_types_serializer.data
      })


class UploadProductImage(ListCreateAPIView):
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
      store_host = self.request.META.get("HTTP_ORIGIN")
      try:
         store = Store.objects.get(domain_name=store_host)
         queryset = MarketPlace.objects.filter(
               store=store, list_product=True).select_related('product').order_by("-id")
         return queryset
      except Store.DoesNotExist:
         logging.error("Store with ID %s does not exist." % store_id)
         return MarketPlace.objects.none()


# Get Dropshipper Store Counts
class DropshipperDashboardCounts(APIView):
   def get(self, request):
      # Get Store
      store_id = request.query_params.get("mall")
      store = get_object_or_404(Store, id=store_id)

      # Get Number of Listed Products
      product_count = MarketPlace.objects.filter(
         store=store.id, list_product=True).count()

      # # Get Number of all Orders per store
      order_count = StoreOrder.objects.filter(store=store).count()

      # Get Number of Customers
      customer_count = CustomUser.objects.filter(
         associated_domain=store).count()

      data = {
         "Listed_Products": product_count,
         "Orders": order_count,
         "Customers": customer_count
      }
      return Response(data, status=status.HTTP_200_OK)


# Best Selling Product Data
class BestSellingProductView(ListAPIView):
   serializer_class = ProductSerializer
   
   def get_queryset(self):
      return Product.objects.all().order_by('-sales_count')[:3]


class StoreOrdersViewSet(ListAPIView):
   serializer_class = OrderSerializer

   def get_queryset(self):
      store_id = self.request.domain_name
      verified_store = get_object_or_404(Store, id=store_id)

      # Use a try-except block to handle the case where no orders are found for the given store
      try:
         orders = StoreOrder.objects.filter(store=verified_store).select_related('buyer', 'store')
      except StoreOrder.DoesNotExist:
         return StoreOrder.objects.none()
      return orders

   # def get_store(self, store_id):
   #    try:
   #       store = Store.objects.get(id=store_id)
   #    except Store.DoesNotExist:
   #       # Instead of returning a ValidationError, raise a serializers.ValidationError
   #       raise serializers.ValidationError("Store Does Not Exist")

   #    return store


class BrandView(viewsets.ModelViewSet):
   queryset = Brand.objects.prefetch_related('producttype')
   serializer_class = BrandSerializer


class SubCategoryView(viewsets.ModelViewSet):
   queryset =  SubCategories.objects.select_related('category')
   serializer_class = SubCategorySerializer


class ProductTypeView(viewsets.ModelViewSet):
   queryset = ProductTypes.objects.select_related('subcategory')
   serializer_class = ProductTypesSerializer


class ProductDetails(viewsets.ModelViewSet):
   queryset = Product.objects.select_related('category', 'subcategory', 'producttype', 'brand').prefetch_related('store', 'images', 'product_variants')
   serializer_class = ProductDetailSerializer


class WalletView(viewsets.ModelViewSet):
   queryset = Wallet.objects.select_related('store')
   serializer_class = WalletSerializer
   lookup_field = 'store_id'  # Disable the default lookup field


class ServicesBusinessInformationView(viewsets.ModelViewSet):
   queryset = ServicesBusinessInformation.objects.select_related('user')
   serializer_class = ServicesBusinessInformationSerializer
