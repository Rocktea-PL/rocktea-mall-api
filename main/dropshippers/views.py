from mall.models import CustomUser, Product, Category
from mall.serializers import ProductSerializer
from rest_framework.generics import ListAPIView
from django.shortcuts import get_list_or_404

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .serializers import DropshipperAdminSerializer, DropshipperListSerializer, DropshipperDetailSerializer

from django.db.models import Count, Sum, Q, Case, When, BooleanField, DecimalField, IntegerField, Prefetch
from django.db.models.functions import Coalesce
from mall.models import Product
from order.models import StoreOrder
from mall.models import StoreProductPricing

from django.utils import timezone
from order.pagination import CustomPagination

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .filters import DropshipperFilter
from django.core.cache import cache

# Create your views here.
# Get Store Products by Category
class MyProducts(ListAPIView):
   serializer_class = ProductSerializer

   def get_queryset(self, *args, **kwargs):
      category = self.request.query_params.get("category")
      
      if not category:
         return Product.objects.none()
      
      try:
         verified_category = get_list_or_404(Category, id=category)
         return Product.objects.filter(category__in=verified_category).select_related('category')
      except:
         return Product.objects.none()

class DropshipperAdminViewSet(viewsets.ModelViewSet):
   """Optimized admin-only dropshipper management with analytics"""
   permission_classes = [IsAdminUser]
   lookup_field = 'id'
   pagination_class = CustomPagination

   filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
   filterset_class = DropshipperFilter
   search_fields = ['email', 'first_name', 'last_name', 'owners__name']
   ordering_fields = ['date_joined', 'last_login', 'total_revenue']
   ordering = ['-date_joined']

   def get_serializer_class(self):
      if self.action == 'list':
         return DropshipperListSerializer
      elif self.action == 'create':
         return DropshipperAdminSerializer
      return DropshipperDetailSerializer

   def destroy(self, request, *args, **kwargs):
      try:
         instance = self.get_object()

         # Safe image deletion
         if hasattr(instance, 'profile_image') and instance.profile_image:
            try:
               instance.profile_image.delete()
            except Exception as e:
               print(f"Image deletion error: {str(e)}")
         
         # Delete related store (cascade handles the rest)
         if hasattr(instance, 'owners') and instance.owners:
            instance.owners.delete()
            
         self.perform_destroy(instance)
         return Response(status=status.HTTP_204_NO_CONTENT)
      except Exception as e:
         return Response({
            'error': 'Failed to delete dropshipper',
            'details': str(e)
         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   def create(self, request, *args, **kwargs):
      try:
         serializer = self.get_serializer(data=request.data)
         serializer.is_valid(raise_exception=True)
         self.perform_create(serializer)
         
         # Return basic user data
         return Response({
            'id': serializer.instance.id,
            'email': serializer.instance.email,
            'first_name': serializer.instance.first_name,
            'last_name': serializer.instance.last_name,
            'is_store_owner': serializer.instance.is_store_owner,
            'date_joined': serializer.instance.date_joined
         }, status=status.HTTP_201_CREATED)
      except Exception as e:
         return Response({
            'error': 'Failed to create dropshipper',
            'details': str(e)
         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   def update(self, request, *args, **kwargs):
      try:
         partial = kwargs.pop('partial', False)
         instance = self.get_object()
         
         serializer = self.get_serializer(instance, data=request.data, partial=partial)
         serializer.is_valid(raise_exception=True)
         self.perform_update(serializer)
         
         return Response({
            'id': instance.id,
            'email': instance.email,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'is_active': instance.is_active,
            'last_login': instance.last_login
         })
      except Exception as e:
         return Response({
            'error': 'Failed to update dropshipper',
            'details': str(e)
         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
   def get_queryset(self):
      # Simple query to avoid complex annotations that might fail
      return CustomUser.objects.filter(
         is_store_owner=True
      ).select_related('owners').order_by('-date_joined')
   
   http_method_names = ['get', 'post', 'put', 'patch', 'delete']