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
      
      # Cache category lookup
      cache_key = f"category_{category}"
      verified_category = cache.get(cache_key)
      
      if not verified_category:
         verified_category = get_list_or_404(Category, id=category)
         cache.set(cache_key, verified_category, 300)
      
      return Product.objects.filter(category__in=verified_category).select_related('category')

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
      instance = self.get_object()

      # Safe image deletion
      if instance.profile_image:
         try:
            instance.profile_image.delete()
         except Exception as e:
            print(f"Cloudinary deletion error: {str(e)}")
      
      # Delete related store (cascade handles the rest)
      if hasattr(instance, 'owners'):
         instance.owners.delete()
         
      self.perform_destroy(instance)
      return Response(status=status.HTTP_204_NO_CONTENT)

   def create(self, request, *args, **kwargs):
      serializer = self.get_serializer(data=request.data)
      serializer.is_valid(raise_exception=True)
      self.perform_create(serializer)
      
      # Return created instance with full details
      output_serializer = DropshipperDetailSerializer(
         serializer.instance, 
         context=self.get_serializer_context()
      )
      return Response(output_serializer.data, status=status.HTTP_201_CREATED)

   def update(self, request, *args, **kwargs):
      partial = kwargs.pop('partial', False)
      instance = self.get_object()
      
      # Skip DNS updates in admin context
      context = self.get_serializer_context()
      context['skip_dns_update'] = True
      
      serializer = self.get_serializer(instance, data=request.data, partial=partial, context=context)
      serializer.is_valid(raise_exception=True)
      self.perform_update(serializer)
      
      output_serializer = DropshipperDetailSerializer(instance, context=context)
      return Response(output_serializer.data)
   
   def get_queryset(self):
      now = timezone.now()
      thirty_days_ago = now - timezone.timedelta(days=30)
      
      # Optimized query with single database hit
      return CustomUser.objects.filter(
         is_store_owner=True
      ).select_related('owners').prefetch_related(
         Prefetch(
            'owners__store_orders',
            queryset=StoreOrder.objects.filter(status='Completed').only('total_price')
         ),
         Prefetch(
            'owners__pricings',
            queryset=StoreProductPricing.objects.select_related('product').only('product__is_available')
         )
      ).annotate(
         # Pre-calculate all metrics in database
         total_products=Count('owners__pricings', distinct=True),
         total_products_available=Count(
            'owners__pricings',
            filter=Q(owners__pricings__product__is_available=True),
            distinct=True
         ),
         total_products_sold=Coalesce(
            Sum('owners__store_orders__items__quantity', 
                filter=Q(owners__store_orders__status='Completed')), 
            0
         ),
         total_revenue=Coalesce(
            Sum('owners__store_orders__total_price',
                filter=Q(owners__store_orders__status='Completed')), 
            0.0
         ),
         is_active_user=Case(
            When(last_login__gte=thirty_days_ago, then=True),
            default=False,
            output_field=BooleanField()
         )
      )