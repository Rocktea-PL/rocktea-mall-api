from mall.models import CustomUser, Store, Product, Category
from mall.serializers import ProductSerializer
from rest_framework.generics import RetrieveAPIView, ListAPIView
from django.shortcuts import get_object_or_404, get_list_or_404

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .serializers import DropshipperAdminSerializer, DropshipperListSerializer

from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Sum, Q, Case, When, BooleanField, DecimalField, IntegerField, CharField, Value
from django.db.models.functions import Coalesce
from mall.models import Product 

from django.utils import timezone

# Create your views here.
# Get Store Products by Category
class MyProducts(ListAPIView):
   serializer_class = ProductSerializer

   def get_queryset(self, *args, **kwargs):
      category = self.request.query_params.get("category")
      
      # Verify category using get_list_or_404
      verified_category = get_list_or_404(Category, id=category)
      
      # Filter Product By Category
      queryset = Product.objects.filter(category__in=verified_category)
      return queryset
   
class DropshipperPagination(PageNumberPagination):
   """Custom pagination for dropshippers"""
   page_size = 20
   page_size_query_param = 'page_size'
   max_page_size = 100

class DropshipperAdminViewSet(viewsets.ModelViewSet):
   """
   Admin-only dropshipper management with analytics
   """
   queryset = CustomUser.objects.filter(is_store_owner=True)
   serializer_class = DropshipperAdminSerializer
   permission_classes = [IsAdminUser]
   lookup_field = 'id'
   pagination_class = DropshipperPagination

   def get_serializer_class(self):
      if self.action == 'list':
         return DropshipperListSerializer
      return DropshipperAdminSerializer

   def update(self, request, *args, **kwargs):
      """Handle full update - signals will manage Cloudinary deletion"""
      return super().update(request, *args, **kwargs)

   def partial_update(self, request, *args, **kwargs):
      """Handle partial update - signals will manage Cloudinary deletion"""
      return super().partial_update(request, *args, **kwargs)

   def destroy(self, request, *args, **kwargs):
      instance = self.get_object()

      # Delete profile image first
      if instance.profile_image:
         try:
               instance.profile_image.delete()
         except Exception as e:
               print(f"Cloudinary deletion error: {str(e)}")
      
      # Delete related store and products
      if hasattr(instance, 'owners'):
         instance.owners.delete()  # Cascade delete store and related objects
         
      self.perform_destroy(instance)
      return Response(status=status.HTTP_204_NO_CONTENT)

   def perform_create(self, serializer):
      serializer.save(is_store_owner=True)  # Force store owner status

   def get_queryset(self):
      now = timezone.now()
      thirty_days_ago = now - timezone.timedelta(days=30)
      
      return super().get_queryset().select_related('owners').annotate(
         # Store metrics
         total_products=Count('owners__pricings', distinct=True),
         total_products_available=Count(
            'owners__pricings',
            filter=Q(owners__pricings__product__is_available=True),
            distinct=True
         ),
         total_products_sold=Coalesce(
            Sum(
               'owners__store_orders__items__quantity',
               filter=Q(owners__store_orders__status='Completed'),
               output_field=IntegerField()  # Explicit output field
            ), 
            0, 
            output_field=IntegerField()
         ),
         total_revenue=Coalesce(
            Sum(
               'owners__store_orders__total_price',
               filter=Q(owners__store_orders__status='Completed'),
               output_field=DecimalField(max_digits=12, decimal_places=2)
            ), 
            0.0,
            output_field=DecimalField(max_digits=12, decimal_places=2)
         ),
         
         # Activity status
         is_active_user=Case(
            When(last_login__gte=thirty_days_ago, then=True),
            default=False,
            output_field=BooleanField()
         )
      ).order_by('-date_joined')