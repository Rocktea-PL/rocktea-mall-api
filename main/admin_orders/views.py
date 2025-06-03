from django.http import Http404
from rest_framework import viewsets, status
from order.models import StoreOrder, OrderItems, PaystackWebhook
from .serializers import AdminOrderSerializer, AdminTransactionSerializer
from order.pagination import CustomPagination
from django.db.models import Prefetch
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

class AdminOrderViewSet(viewsets.ModelViewSet):
    serializer_class = AdminOrderSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    http_method_names = ['get']
    lookup_field = 'identifier'

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'created_at': ['exact', 'gte', 'lte'],
        'buyer__email': ['exact', 'contains'],
        'store__name': ['exact', 'contains'],
        'total_price': ['exact', 'gte', 'lte'],
        'delivery_code': ['exact'],
        'tracking_id': ['exact'],
    }
    search_fields = ['id', 'order_sn', 'delivery_location']
    ordering_fields = ['created_at', 'total_price']
    
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
        
class AdminTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = AdminTransactionSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    http_method_names = ['get']

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'created_at': ['exact', 'gte', 'lte'],
        'user__email': ['exact', 'contains'],
        'order__id': ['exact'],
        'total_price': ['exact', 'gte', 'lte'],
        'purpose': ['exact'],
        'reference': ['exact'],
    }
    search_fields = ['reference', 'user__email']
    ordering_fields = ['created_at', 'total_price']
    
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