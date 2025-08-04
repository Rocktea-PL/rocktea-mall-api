from mall.models import CustomUser, Product, Category
from mall.serializers import ProductSerializer
from rest_framework.generics import ListAPIView
from django.shortcuts import get_list_or_404

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .serializers import DropshipperAdminSerializer, DropshipperListSerializer, DropshipperDetailSerializer

from django.db.models import Count, Sum, Q, Case, When, BooleanField, DecimalField, IntegerField, CharField, Value
from django.db.models.functions import Coalesce
from mall.models import Product 

from django.utils import timezone
from order.pagination import CustomPagination

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .filters import DropshipperFilter

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

class DropshipperAdminViewSet(viewsets.ModelViewSet):
   """Admin-only dropshipper management with analytics"""
   queryset = CustomUser.objects.filter(is_store_owner=True)
   permission_classes = [IsAdminUser]
   lookup_field = 'id'
   pagination_class = CustomPagination

   filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
   filterset_class = DropshipperFilter
   search_fields = ['email', 'first_name', 'last_name', 'owners__name']
   ordering_fields = ['date_joined', 'last_login', 'total_revenue']

   def get_serializer_class(self):
    if self.action == 'list':
        return DropshipperListSerializer
    elif self.action == 'create':
        return DropshipperAdminSerializer
    elif self.action in ['retrieve', 'update', 'partial_update']:
        return DropshipperDetailSerializer

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

   def create(self, request, *args, **kwargs):
      """Handle creation with proper response formatting"""
      serializer = self.get_serializer(data=request.data)
      serializer.is_valid(raise_exception=True)
      self.perform_create(serializer)
      
      # Return the created instance with full details
      instance = serializer.instance
      output_serializer = DropshipperDetailSerializer(instance, context=self.get_serializer_context())
      headers = self.get_success_headers(output_serializer.data)
      return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

   def update(self, request, *args, **kwargs):
      """Handle update with proper response formatting - no DNS updates"""
      partial = kwargs.pop('partial', False)
      instance = self.get_object()
      
      # Prevent DNS record updates by setting context flag
      context = self.get_serializer_context()
      context['skip_dns_update'] = True
      
      serializer = self.get_serializer(instance, data=request.data, partial=partial, context=context)
      serializer.is_valid(raise_exception=True)
      self.perform_update(serializer)
      
      # Return the updated instance with full details
      output_serializer = DropshipperDetailSerializer(instance, context=self.get_serializer_context())
      return Response(output_serializer.data)
   
   def get_queryset(self):
      now = timezone.now()
      thirty_days_ago = now - timezone.timedelta(days=30)
      
      return super().get_queryset().select_related('owners').prefetch_related(
         'owners__store_orders'
      ).annotate(
         # Store metrics
         total_products=Coalesce(
            Count('owners__pricings', distinct=True),
            0,
            output_field=IntegerField()
         ),
         total_products_available=Coalesce(
            Count(
               'owners__pricings',
               filter=Q(owners__pricings__product__is_available=True),
               distinct=True
            ),
            0,
            output_field=IntegerField()
         ),
         total_products_sold=Coalesce(
            Sum(
               'owners__store_orders__items__quantity',
               filter=Q(owners__store_orders__status='Completed'),
               output_field=IntegerField()
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