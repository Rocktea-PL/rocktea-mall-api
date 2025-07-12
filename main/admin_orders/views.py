from django.http import Http404
from rest_framework import viewsets, status, filters
from order.models import StoreOrder, OrderItems, PaystackWebhook
from .serializers import AdminOrderSerializer, AdminTransactionSerializer
from order.pagination import CustomPagination
from django.db.models import Prefetch
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters


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
    search_fields = [
        'id',  # Matches order_id
        'order_sn',  # Matches invoice_no
        'status',
        'total_price',  # Matches total
        'delivery_location',
        'tracking_id',
        'delivery_code',
        'buyer__first_name',  # For buyer_name
        'buyer__last_name',  # For buyer_name
        'buyer__contact',  # For buyer_contact
        'items__product__name',  # For product_name in items
        'items__product__sku',  # For product_sku in items
    ]
    ordering_fields = ['created_at', 'total_price']

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        
        # Handle custom filters
        params = self.request.query_params
        
        # Handle buyer_email filter
        if 'buyer_email' in params:
            queryset = queryset.filter(buyer__email__icontains=params['buyer_email'])
            
        # Handle store_name filter
        if 'store_name' in params:
            queryset = queryset.filter(store__name__icontains=params['store_name'])
            
        return queryset
    
    def get_queryset(self):
        queryset = StoreOrder.objects.select_related(
            'buyer', 'store'
        ).prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItems.objects.select_related(
                    'product', 'product_variant'
                ).prefetch_related(
                    'product__images',
                    'product__product_variants'  # Prefetch variants
                )
            )
        ).order_by("-created_at")
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset

    def get_object(self):
        # Get the identifier from URL
        identifier = self.kwargs.get('identifier')
        
        try:
            # Try to find by UUID (primary key)
            return self.get_queryset().get(id=identifier)
        except (StoreOrder.DoesNotExist, ValueError):
            try:
                # Try to find by invoice number (order_sn)
                return self.get_queryset().get(order_sn=identifier)
            except StoreOrder.DoesNotExist:
                # Try to find by delivery code
                try:
                    return self.get_queryset().get(delivery_code=identifier)
                except StoreOrder.DoesNotExist:
                    raise Http404("No order found with the provided identifier")

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Http404:
            return Response(
                {
                    "error": "Order not found",
                    "message": "No order exists with the provided identifier. "
                               "Please check the order ID."
                },
                status=status.HTTP_404_NOT_FOUND
            )

class TransactionFilter(django_filters.FilterSet):
    user_email = django_filters.CharFilter(field_name="user__email", lookup_expr='icontains')
    order_id = django_filters.CharFilter(field_name="order__id")
    
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
    lookup_field = 'id'
    lookup_url_kwarg = 'id'

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = [
        'reference',
        'total_price',
        'status',
        'user__email',
        'user__first_name',
        'user__last_name',
        'order__order_sn',
        'order__id',
    ]
    ordering_fields = ['created_at', 'total_price']

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        
        # Handle custom filters
        params = self.request.query_params
        
        # Handle user_email filter
        if 'user_email' in params:
            queryset = queryset.filter(user__email__icontains=params['user_email'])
            
        # Handle order_id filter
        if 'order_id' in params:
            queryset = queryset.filter(order__id=params['order_id'])
            
        return queryset
    
    def get_queryset(self):
        queryset = PaystackWebhook.objects.select_related(
            'user', 'order'
        ).order_by("-created_at")
        
        # Optional filtering
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        purpose = self.request.query_params.get('purpose')
        if purpose:
            queryset = queryset.filter(purpose=purpose)
            
        return queryset
    