from django.http import Http404
from rest_framework import viewsets, status, filters
from order.models import StoreOrder, OrderItems, PaystackWebhook
from .serializers import AdminOrderSerializer, AdminTransactionSerializer
from order.pagination import CustomPagination
from django.db.models import Prefetch, Count, Q
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from django.core.cache import cache


class OrderFilter(django_filters.FilterSet):
    buyer_email = django_filters.CharFilter(field_name="buyer__email", lookup_expr='icontains')
    store_name = django_filters.CharFilter(field_name="store__name", lookup_expr='icontains')
    
    class Meta:
        model = StoreOrder
        fields = {
            'status': ['exact', 'in'],
            'created_at': ['exact', 'gte', 'lte'],
            'total_price': ['exact', 'gte', 'lte'],
            'delivery_code': ['exact'],
            'tracking_id': ['exact'],
        }

class AdminOrderViewSet(viewsets.ModelViewSet):
    serializer_class = AdminOrderSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    http_method_names = ['get']
    lookup_field = 'identifier'

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OrderFilter
    search_fields = ['id', 'order_sn', 'status', 'buyer__email', 'store__name']
    ordering_fields = ['created_at', 'total_price']
    ordering = ['-created_at']


    
    def get_queryset(self):
        # Optimized query with minimal joins
        return StoreOrder.objects.select_related(
            'buyer', 'store'
        ).prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItems.objects.select_related(
                    'product', 'product_variant'
                ).prefetch_related('product__images')
            )
        ).annotate(
            item_count=Count('items')
        )

    def get_object(self):
        identifier = self.kwargs.get('identifier')
        cache_key = f"admin_order_{identifier}"
        
        # Try cache first
        cached_order = cache.get(cache_key)
        if cached_order:
            return cached_order
        
        try:
            # Try UUID first, then order_sn, then delivery_code
            order = self.get_queryset().get(
                Q(id=identifier) | Q(order_sn=identifier) | Q(delivery_code=identifier)
            )
            cache.set(cache_key, order, 300)  # Cache for 5 minutes
            return order
        except (StoreOrder.DoesNotExist, StoreOrder.MultipleObjectsReturned):
            raise Http404("No order found with the provided identifier")

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Http404:
            return Response({
                "error": "Order not found",
                "message": "No order exists with the provided identifier."
            }, status=status.HTTP_404_NOT_FOUND)

class TransactionFilter(django_filters.FilterSet):
    user_email = django_filters.CharFilter(field_name="user__email", lookup_expr='icontains')
    
    class Meta:
        model = PaystackWebhook
        fields = {
            'status': ['exact', 'in'],
            'created_at': ['exact', 'gte', 'lte'],
            'total_price': ['exact', 'gte', 'lte'],
            'purpose': ['exact'],
            'reference': ['exact'],
        }

class AdminTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = AdminTransactionSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = ['reference', 'user__email', 'order__order_sn']
    ordering_fields = ['created_at', 'total_price']
    ordering = ['-created_at']


    
    def get_queryset(self):
        return PaystackWebhook.objects.select_related('user', 'order')
    