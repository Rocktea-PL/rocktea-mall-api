# from rest_framework import viewsets
from .serializers import (
   SimpleProductSerializer,
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
   OperationsSerializer,
   NotificationSerializer,
   PromoPlanSerializer,
   BuyerBehaviourSerializer,
   ShippingDataSerializer,
   ProductReviewSerializer,
   ProductRatingSerializer,
   DropshipperReviewSerializer,
   ResetPasswordEmailRequestSerializer,
   ResetPasswordConfirmSerializer
)
from django.http import Http404
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
   Wallet,
   Notification,
   PromoPlans,
   BuyerBehaviour,
   ShippingData,
   ProductReview,
   DropshipperReview,
   ProductRating
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
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.decorators import action
from helpers.views import BaseView
from django.db import transaction
from .task import upload_image
from django.db.models import Count
from django.core.cache import cache
import logging
from .store_features.get_store_id import get_store_instance
from workshop.processor import DomainNameHandler
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import IsAdminOrReadOnly, IsAuthenticatedOrReadOnly, IsStoreOwnerOrAdminDelete, IsStoreOwnerOrAdminViewAdd
from django_rest_passwordreset.views import ResetPasswordRequestToken, ResetPasswordConfirm
from rest_framework import generics
from django.core.mail import send_mail
from setup.utils import sendEmail

from django.conf import settings
from django.urls import reverse
from django_rest_passwordreset.models import ResetPasswordToken
from django_rest_passwordreset.signals import reset_password_token_created
from django.dispatch import receiver
from django.contrib.sites.shortcuts import get_current_site
from urllib.parse import urlparse

from order.pagination import CustomPagination
from django.db.models import Sum, Count, Q
from setup.utils import get_store_domain
from django.utils import timezone

handler = DomainNameHandler()

# Set up logging
logger = logging.getLogger(__name__)

# Create your views here.
# TODO DONE
class CreateStoreOwner(viewsets.ModelViewSet):
   """
   Sign Up Store Owners Feature
   """
   queryset = CustomUser.objects.select_related('associated_domain')
   serializer_class = StoreOwnerSerializer
   renderer_classes= [JSONRenderer]
   
   def get_queryset(self):
      user_id =  self.request.query_params.get("mallcli")

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
      # This queryset is for retrieving existing stores, not for creation.
      # It correctly filters based on the domain from the request.
      domain = handler.process_request(store_domain=get_store_domain(self.request))
      # Filter stores based on domain_name
      queryset = Store.objects.filter(id=domain)
      return queryset
   
   def perform_create(self, serializer):
      # DRF's perform_create automatically passes request.user to serializer.save()
      # when serializer.create() is called.
      # We need to ensure the request object is available in the serializer context
      # for the signal to access get_current_site (or request.get_host()).
      serializer.save()
   
   def get_serializer_context(self):
      # Crucial for passing the request to the serializer's create method
      # and subsequently to the signal.
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
   permission_classes = [IsAuthenticatedOrReadOnly]
   pagination_class = CustomPagination

   def get_queryset(self):
      category_id = self.request.query_params.get('category')
      if category_id is not None:
         category = get_object_or_404(Category, id=category_id)
         return Product.objects.filter(category=category).select_related("category", "subcategory", "producttype", "brand").prefetch_related("images", "store", 'product_variants')
      else:
         return Product.objects.select_related("category", "subcategory", "producttype", "brand").prefetch_related("images", "store", 'product_variants')

   @transaction.atomic
   def perform_create(self, serializer):
      product = serializer.save()
      if product:
         return Response({"message": "Product Created Successfully"}, status=status.HTTP_201_CREATED)
      return Response({"error": "Error occurs while creating product"}, status=status.HTTP_400_BAD_REQUEST)

   def list(self, request, *args, **kwargs):
      """Override the list method to disable pagination for the main GET request."""
      queryset = self.get_queryset()
      serializer = self.get_serializer(queryset, many=True)
      return Response(serializer.data)

   @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='by-shop')
   def my_products_list(self, request):
      
      store = getattr(request.user, 'owners', None)
      if not store:
         return Response(
               {"error": "You are not associated with a store."},
               status=status.HTTP_400_BAD_REQUEST
         )

      try:
         # Get summary data
         total_products_added = StoreProductPricing.objects.filter(store=store).count()
         total_products_available = Product.objects.filter(
               id__in=StoreProductPricing.objects.filter(store=store).values_list('product', flat=True),
               is_available=True
         ).count()
         # Calculate total products sold
         store_orders = StoreOrder.objects.filter(
            store=store
         )

         # Calculate total products sold
         total_products_sold = sum(
            sum(item.quantity for item in order.items.all())
            for order in store_orders
         )

         summary = {
            "total_products_added": total_products_added,
            "total_products_available": total_products_available,
            "total_products_sold": total_products_sold,
         }

         # Optimize product query using `select_related` and `prefetch_related`
         store_product_pricings = StoreProductPricing.objects.filter(store=store).select_related('product')

         # Apply custom pagination
         paginator = CustomPagination()
         paginated_data = paginator.paginate_queryset(store_product_pricings, request)

         # Serialize the paginated data with context
         serializer = SimpleProductSerializer(
               [pricing.product for pricing in paginated_data],
               many=True,
               context={'store': store}
         )

         # Combine the summary and paginated data in the response
         return paginator.get_paginated_response({
               "summary": summary,
               "products": serializer.data
         })

      except Exception as e:
         # Handle unexpected errors
         print(f"Error fetching products for the store: {e}")
         return Response(
               {"error": "An error occurred while retrieving the store's products."},
               status=status.HTTP_500_INTERNAL_SERVER_ERROR
         )
      
   @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated], url_path='remove-from-store')
   @transaction.atomic
   def remove_product_from_store(self, request, pk=None):
      """
      Allows store owners to remove a product from a specific store they own
      """
      # Extract store ID from query parameters
      store_id = request.query_params.get('mall')
      if not store_id:
         return Response(
               {"error": "Missing 'mall' query parameter specifying the store ID."},
               status=status.HTTP_400_BAD_REQUEST
         )
      
      # Validate store existence and user ownership
      try:
         store = Store.objects.get(id=store_id)
      except Store.DoesNotExist:
         return Response(
               {"error": "Store not found."},
               status=status.HTTP_404_NOT_FOUND
         )
      
      # Check if user owns the store
      if not request.user.is_superuser and not store.owners.filter(id=request.user.id).exists():
         return Response(
               {"error": "You are not an owner of this store."},
               status=status.HTTP_403_FORBIDDEN
         )
      
      # Get the product
      product = get_object_or_404(Product, pk=pk)
      
      # Remove product-store association
      pricing = StoreProductPricing.objects.filter(store=store, product=product).first()
      if not pricing:
         return Response(
               {"error": "This product is not available in your store."},
               status=status.HTTP_400_BAD_REQUEST
         )
      
      pricing.delete()
      return Response(
         {"message": "Product successfully removed from your store"},
         status=status.HTTP_204_NO_CONTENT
      )
      
class ProductRatingViewSet(viewsets.ModelViewSet):
   queryset = ProductRating.objects.select_related("product")
   serializer_class = ProductRatingSerializer

class ProductFilter(ListAPIView):
   queryset = Product.objects.select_related('category', 'subcategory', 'producttype', 'brand').prefetch_related('store', 'images', 'product_variants')
   serializer_class = ProductSerializer
   filter_backends = [DjangoFilterBackend]
   filterset_fields = ["category", "producttype", "subcategory"]

   # def get_queryset(self):
   #    queryset = super().get_queryset()
   #    print("Original queryset:", queryset)  # Inspect original queryset
   #    filtered_queryset = self.filter_queryset(queryset)
   #    print("Filtered queryset:", filtered_queryset)  # Inspect filtered queryset
   #    return filtered_queryset

class ProductVariantView(viewsets.ModelViewSet):
   queryset = ProductVariant.objects.all().prefetch_related('product')
   serializer_class = ProductVariantSerializer
   permission_classes = [IsAdminOrReadOnly]

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

   def get_permissions(self):
      """
      Assign permissions based on the HTTP method.
      """
      if self.request.method == "GET":
         return [IsStoreOwnerOrAdminViewAdd()]
      elif self.request.method == "DELETE":
         return [IsStoreOwnerOrAdminDelete()]
      return super().get_permissions()

   def post(self, request):
      try:
         collect = request.data
         store = getattr(request.user, 'owners', None)
         if not store:
            return Response(
                  {"error": "You are not associated with a store."},
                  status=status.HTTP_400_BAD_REQUEST
            )
         store_id = store.id
         # store_id = handler.process_request(store_domain=get_store_domain(request))
         product_id = collect.get("product")
         retail_price = collect.get("retail_price")

         # Log the incoming data
         logger.info(f"Creating StoreProductPricing for store: {store_id}, product: {product_id}")

         # Fetch the store and product objects
         store = get_object_or_404(Store, id=store_id)
         product = get_object_or_404(Product, id=product_id)

         # Check if the product pricing is valid before proceeding
         self.validate_product_pricing(store, product)

         # Create the StoreProductPricing instance
         store_product_price = StoreProductPricing.objects.create(
               store=store,
               product=product,
               retail_price=retail_price
         )

         serializer = StoreProductPricingSerializer(store_product_price)
         return Response({"message": "Product pricing validated successfully.", "data": serializer.data})
      except Exception as e:
         # Log the exception
         logger.error(f"Error creating StoreProductPricing: {e}", exc_info=True)
         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

   def validate_product_pricing(self, store, product):
      try:
         existing_pricing = StoreProductPricing.objects.filter(store=store, product=product).exclude(id=None).first()
         if existing_pricing:
               raise serializers.ValidationError("Pricing for this product in this store already exists.")
      except serializers.ValidationError as e:
         # Log the validation error
         logger.warning(f"Validation error in product pricing: {e}")
         raise

   def get(self, request):
      # store_product_prices = StoreProductPricing.objects.all()
      # serializer = StoreProductPricingSerializer(store_product_prices, many=True)
      # return Response(serializer.data, status=status.HTTP_200_OK)
      store_id = handler.process_request(store_domain=get_store_domain(request))
      
      # Get the store instance based on the provided store_id
      store = get_object_or_404(Store, id=store_id)
      
      try:
         # Retrieve all store prices related to the specified store
         store_prices = StoreProductPricing.objects.filter(store=store)
         
         # Serialize the data
         store_prices_serializer = StoreProductPricingSerializer(store_prices, many=True)
         
         # Return the serialized data as the API response
         return Response(store_prices_serializer.data, status=status.HTTP_200_OK)
      
      except Exception as e:
         # Handle exceptions, you might want to log the error or return a different response
         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   # Assuming you have fixed the delete method as well to use request.data properly for product_id
   def delete(self, request):

      try:
         store_id = request.query_params.get("mall")
         product_id = request.data.get("product")  # Make sure this line is corrected to use request.data

         store = get_object_or_404(Store, id=store_id)
         product = get_object_or_404(Product, id=product_id)
         
         store_product_price = StoreProductPricing.objects.get(store=store, product=product)
         store_product_price.delete()
         return Response({"message": "Store product pricing deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
      except Exception as e:
         logger.error(f"Error deleting StoreProductPricing: {e}", exc_info=True)
         return Response({"error": "An error occurred while deleting the store product pricing."}, status=status.HTTP_400_BAD_REQUEST)

class GetStoreProduct(APIView):
   permission_classes = [IsAuthenticated]

   def get(self, request):
      # Retrieve the store associated with the authenticated user
      store = getattr(request.user, 'owners', None)
      if not store:
         return Response(
               {"error": "You are not associated with a store."},
               status=status.HTTP_400_BAD_REQUEST
         )

      try:
         # Query the store's product pricing records
         store_product_pricings = StoreProductPricing.objects.filter(store=store)

         # Retrieve the products related to the store
         products = [pricing.product for pricing in store_product_pricings]

         # Serialize the product data with the store context
         serializer = SimpleProductSerializer(
               products, many=True, context={'store': store}
         )
         return Response(serializer.data, status=status.HTTP_200_OK)

      except Exception as e:
         # Handle unexpected errors
         print(f"Error fetching products for the store: {e}")
         return Response(
               {"error": "An error occurred while retrieving the store's products."},
               status=status.HTTP_500_INTERNAL_SERVER_ERROR
         )

# Depreciated
class StoreProductPricingAPIView(APIView):
   renderer_classes = [JSONRenderer]

   def get_permissions(self):
      """
      Assign permissions based on the HTTP method.
      """
      if self.request.method == "GET":
         return [IsStoreOwnerOrAdminViewAdd()]
      elif self.request.method == "DELETE":
         return [IsStoreOwnerOrAdminDelete()]
      return super().get_permissions()

   def get(self, request):
      store_id = handler.process_request(store_domain=get_store_domain(request))
      
      # Get the store instance based on the provided store_id
      store = get_object_or_404(Store, id=store_id)
      
      try:
         # Retrieve all store prices related to the specified store
         store_prices = StoreProductPricing.objects.filter(store=store)
         
         # Serialize the data
         store_prices_serializer = StoreProductPricingSerializer(store_prices, many=True)
         
         # Return the serialized data as the API response
         return Response(store_prices_serializer.data, status=status.HTTP_200_OK)
      
      except Exception as e:
         # Handle exceptions, you might want to log the error or return a different response
         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   def delete(self, request):
      store_id = request.query_params.get("store_id")
      product_id = request.query_params.get("product_id")
      try:
         # Get the store price to be deleted
         store_price = StoreProductPricing.objects.get(store_id=store_id, product_id=product_id)

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
         'product_types': product_types_serializer.data,
         # 'brand': brand_serializer.data
      })

class CategoryViewSet(viewsets.ModelViewSet):
   queryset = Category.objects.all()
   serializer_class = CategorySerializer
   permission_classes = [IsAuthenticated, IsAdminUser]

   def create(self, request, *args, **kwargs):
      serializer = self.get_serializer(data=request.data)
      serializer.is_valid(raise_exception=True)
      self.perform_create(serializer)
      headers = self.get_success_headers(serializer.data)
      return Response(
         {
               'message': 'Category created successfully',
               'data': serializer.data
         },
         status=status.HTTP_201_CREATED, 
         headers=headers
      )
   
   def update(self, request, *args, **kwargs):
      partial = kwargs.pop('partial', False)
      instance = self.get_object()
      serializer = self.get_serializer(instance, data=request.data, partial=partial)
      serializer.is_valid(raise_exception=True)
      self.perform_update(serializer)
      
      return Response({
         'message': 'Category updated successfully',
         'data': serializer.data
      })
   
   def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

   def destroy(self, request, *args, **kwargs):
      instance = self.get_object()
      
      category_name = instance.name
      self.perform_destroy(instance)
      
      return Response(
         {'message': f'Category "{category_name}" deleted successfully'},
         status=status.HTTP_204_NO_CONTENT
      )

class UploadProductImage(ListCreateAPIView):
   queryset = ProductImage.objects.all()
   serializer_class = ProductImageSerializer
   parser_classes = (MultiPartParser,)
   permission_classes = [IsAuthenticatedOrReadOnly]

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
      store_host = self.request.query_params.get("mall")
      # handler.process_request(store_domain=get_store_domain(self.request)) 
      # self.request.query_params.get("mall")
      store = Store.objects.get(id=store_host)
      try:
         
         queryset = MarketPlace.objects.filter(
               store=store, list_product=True).select_related('product').order_by("-id")
         return queryset
      except Store.DoesNotExist:
         logging.error("Store with ID %s does not exist.", store_host)
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

class SalesCountView(APIView):
   def get_object(self, product_id):
      try:
         return Product.objects.get(pk=product_id)
      except Product.DoesNotExist:
         raise Http404

   def get(self, request, *args, **kwargs):
      product_id = request.query_params.get('id')  # Retrieving product_id from query parameters
      try:
         product = self.get_object(product_id)
      except Http404:
         return Response({"message": "Product does not exist"}, status=404)
      
      sales_count = product.sales_count
      return Response({"sales_count": sales_count})

class ProductReviewViewSet(viewsets.ModelViewSet):
   queryset = ProductReview.objects.select_related("user", "product")
   serializer_class = ProductReviewSerializer
   
class DropshipperReviewViewSet(viewsets.ModelViewSet):
   queryset = DropshipperReview.objects.select_related("user")
   serializer_class = DropshipperReviewSerializer

class StoreOrdersViewSet(ListAPIView):
   serializer_class = OrderSerializer
   pagination_class = CustomPagination

   def get_queryset(self):
      store_id = self.request.query_params.get("mall")
      verified_store = get_object_or_404(Store, id=store_id)

      # Use a try-except block to handle the case where no orders are found for the given store
      try:
         orders = StoreOrder.objects.filter(store=verified_store).select_related('buyer', 'store')
      except StoreOrder.DoesNotExist:
         return StoreOrder.objects.none()
      return orders

class BrandView(viewsets.ModelViewSet):
   queryset = Brand.objects.prefetch_related('producttype')
   serializer_class = BrandSerializer
   permission_classes = [IsAdminOrReadOnly]

   def create(self, request, *args, **kwargs):
      serializer = self.get_serializer(data=request.data)
      serializer.is_valid(raise_exception=True)
      self.perform_create(serializer)
      headers = self.get_success_headers(serializer.data)
      return Response(
         {
               'message': 'Brand created successfully',
               'data': serializer.data
         },
         status=status.HTTP_201_CREATED, 
         headers=headers
      )

   def update(self, request, *args, **kwargs):
      partial = kwargs.pop('partial', False)
      instance = self.get_object()
      serializer = self.get_serializer(instance, data=request.data, partial=partial)
      serializer.is_valid(raise_exception=True)
      self.perform_update(serializer)
      
      return Response({
         'message': 'Brand updated successfully',
         'data': serializer.data
      })

   def partial_update(self, request, *args, **kwargs):
      kwargs['partial'] = True
      return self.update(request, *args, **kwargs)

   def destroy(self, request, *args, **kwargs):
      instance = self.get_object()
      
      # Check if brand has related products
      if Product.objects.filter(brand=instance).exists():
         return Response(
               {'error': 'Cannot delete brand. It has associated products.'},
               status=status.HTTP_400_BAD_REQUEST
         )
      
      brand_name = instance.name
      self.perform_destroy(instance)
      
      return Response(
         {'message': f'Brand "{brand_name}" deleted successfully'},
         status=status.HTTP_204_NO_CONTENT
      )

class SubCategoryView(viewsets.ModelViewSet):
   queryset =  SubCategories.objects.select_related('category')
   serializer_class = SubCategorySerializer
   permission_classes = [IsAdminOrReadOnly]

   def create(self, request, *args, **kwargs):
      serializer = self.get_serializer(data=request.data)
      serializer.is_valid(raise_exception=True)
      self.perform_create(serializer)
      headers = self.get_success_headers(serializer.data)
      return Response(
         {
            'message': 'Subcategory created successfully',
            'data': serializer.data
         },
         status=status.HTTP_201_CREATED, 
         headers=headers
      )

   def update(self, request, *args, **kwargs):
      partial = kwargs.pop('partial', False)
      instance = self.get_object()
      serializer = self.get_serializer(instance, data=request.data, partial=partial)
      serializer.is_valid(raise_exception=True)
      self.perform_update(serializer)
      
      return Response({
         'message': 'Subcategory updated successfully',
         'data': serializer.data
      })

   def partial_update(self, request, *args, **kwargs):
      kwargs['partial'] = True
      return self.update(request, *args, **kwargs)

   def destroy(self, request, *args, **kwargs):
      instance = self.get_object()
      
      subcategory_name = instance.name
      self.perform_destroy(instance)
      
      return Response(
         {'message': f'Subcategory "{subcategory_name}" deleted successfully'},
         status=status.HTTP_204_NO_CONTENT
      )

class ProductTypeView(viewsets.ModelViewSet):
   queryset = ProductTypes.objects.select_related('subcategory')
   serializer_class = ProductTypesSerializer
   permission_classes = [IsAdminOrReadOnly]

   def create(self, request, *args, **kwargs):
      serializer = self.get_serializer(data=request.data)
      serializer.is_valid(raise_exception=True)
      self.perform_create(serializer)
      headers = self.get_success_headers(serializer.data)
      return Response(
         {
               'message': 'Product type created successfully',
               'data': serializer.data
         },
         status=status.HTTP_201_CREATED, 
         headers=headers
      )

   def update(self, request, *args, **kwargs):
      partial = kwargs.pop('partial', False)
      instance = self.get_object()
      serializer = self.get_serializer(instance, data=request.data, partial=partial)
      serializer.is_valid(raise_exception=True)
      self.perform_update(serializer)
      
      return Response({
         'message': 'Product type updated successfully',
         'data': serializer.data
      })

   def partial_update(self, request, *args, **kwargs):
      kwargs['partial'] = True
      return self.update(request, *args, **kwargs)

   def destroy(self, request, *args, **kwargs):
      instance = self.get_object()
      
      # Check if product type has related products
      if Product.objects.filter(producttype=instance).exists():
         return Response(
               {'error': 'Cannot delete product type. It has associated products.'},
               status=status.HTTP_400_BAD_REQUEST
         )
      
      producttype_name = instance.name
      self.perform_destroy(instance)
      
      return Response(
         {'message': f'Product type "{producttype_name}" deleted successfully'},
         status=status.HTTP_204_NO_CONTENT
      )

class ProductDetails(viewsets.ModelViewSet):
   queryset = Product.objects.select_related('category', 'subcategory', 'producttype', 'brand').prefetch_related('store', 'images', 'product_variants')
   serializer_class = ProductDetailSerializer

class WalletView(viewsets.ModelViewSet):
   queryset = Wallet.objects.select_related('store')
   serializer_class = WalletSerializer
   lookup_field = 'store_id'  # Disable the default lookup field
   permission_classes = [IsAuthenticated]

   def get_queryset(self):
      # Ensure users can only see their own wallets
      return Wallet.objects.filter(store__owner_id=self.request.user.id)

   # def perform_create(self, serializer):
   #    # Set the store to the authenticated user's store
   #    store = Store.objects.get(owner_id=self.request.user.id)
   #    serializer.save(store=store)
   @action(detail=False, methods=['post'], url_path='update-wallet', permission_classes=[IsAuthenticated])
   def update_wallet(self, request, *args, **kwargs):
      try:
         store = Store.objects.get(owner_id=request.user.id)
         wallet = Wallet.objects.get(store=store)
         serializer = self.get_serializer(wallet, data=request.data, partial=True)
         serializer.is_valid(raise_exception=True)
         serializer.save()
         return Response(serializer.data, status=status.HTTP_200_OK)
      except Store.DoesNotExist:
         return Response({"detail": "Store not found."}, status=status.HTTP_404_NOT_FOUND)
      except Wallet.DoesNotExist:
         return Response({"detail": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)

class ServicesBusinessInformationView(viewsets.ModelViewSet):
   queryset = ServicesBusinessInformation.objects.select_related('user')
   serializer_class = ServicesBusinessInformationSerializer

class NotificationView(viewsets.ModelViewSet):
   serializer_class = NotificationSerializer

   def get_queryset(self):
      queryset = Notification.objects.select_related('recipient', 'store')

      store_id = self.request.query_params.get('mall')
      recipient_id = self.request.query_params.get('mall_cli')

      if store_id:
         queryset = queryset.filter(store_id=store_id)
      elif recipient_id:
         queryset = queryset.filter(recipient_id=recipient_id)

      try:
         if queryset.exists():
               return queryset
         else:
               return None
      except Exception as e:
         return None

   def list(self, request, *args, **kwargs):
      queryset = self.get_queryset()
      if queryset is None:
         return Response(status=status.HTTP_204_NO_CONTENT)
      serializer = self.get_serializer(queryset, many=True)
      return Response(serializer.data)

class PromoPlansView(viewsets.ModelViewSet):
   queryset = PromoPlans.objects.select_related('store', 'category')
   serializer_class = PromoPlanSerializer
      
class BuyerBehaviourView(viewsets.ModelViewSet):
   queryset = BuyerBehaviour.objects.select_related('user')
   serializer_class = BuyerBehaviourSerializer
   
class ShippingDataView(viewsets.ModelViewSet):
   queryset = ShippingData.objects.select_related('user')
   serializer_class = ShippingDataSerializer

class CustomResetPasswordRequestToken(ResetPasswordRequestToken):
   serializer_class = ResetPasswordEmailRequestSerializer

   def post(self, request, *args, **kwargs):
      response = super().post(request, *args, **kwargs)
      return response

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
   request = instance.request
   current_site = get_current_site(request=request).domain
   get_protocol = request.scheme
   relative_link = reverse('password_reset_confirm', kwargs={'token': reset_password_token.key})
   absurl = f"{get_protocol}://{current_site}{relative_link}"

   referer = request.META.get('HTTP_REFERER')
   if referer and 'swagger' not in referer.lower():
      parsed_referer = urlparse(referer)
      base_url = f"{parsed_referer.scheme}://{parsed_referer.hostname}/reset-password?token={reset_password_token.key}"
   else:
      base_url = absurl

   subject = "Reset your password - Rockteamall!"

   context = {
      'full_name': reset_password_token.user.get_full_name() or reset_password_token.user.email, # Pass full_name or email
      'confirmation_url': base_url,
      'current_year': timezone.now().year,
   }

   sendEmail(
      recipientEmail=reset_password_token.user.email,
      template_name='emails/reset_email.html',
      context=context,
      subject=subject,
      tags=["forgot-password", "reset-email"]
   )

class CustomResetPasswordConfirm(generics.GenericAPIView):
   serializer_class = ResetPasswordConfirmSerializer

   def post(self, request, *args, **kwargs):
      serializer = self.get_serializer(data=request.data)
      serializer.is_valid(raise_exception=True)

      token = serializer.validated_data['token']
      password = serializer.validated_data['password']

      try:
         reset_password_token = ResetPasswordToken.objects.get(key=token)
         user = reset_password_token.user
         user.set_password(password)
         user.save()

         # Optionally, you can delete the token after successful password reset
         reset_password_token.delete()

         return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
      except ResetPasswordToken.DoesNotExist:
         return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)