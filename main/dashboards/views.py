from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status as drf_status
from django.db.models import (
    Count, Sum, Value, DecimalField, IntegerField, Q, F,
    When, Case, CharField, Prefetch
)
from django.db.models.functions import Coalesce
from order.pagination import CustomPagination
from order.models import StoreOrder, PaystackWebhook, Product
from mall.models import CustomUser
from admin_orders.serializers import AdminTransactionSerializer
from django.utils import timezone
from django.core.cache import cache

class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination

    def get(self, request):
        # Cache dashboard stats for 5 minutes
        cache_key = "admin_dashboard_stats"
        stats = cache.get(cache_key)
        
        if not stats:
            # Single optimized query for all stats
            transaction_stats = PaystackWebhook.objects.filter(
                purpose='order', status='Success'
            ).aggregate(
                total_amount=Coalesce(Sum('total_price'), Value(0)),
                total_count=Count('id')
            )
            
            stats = {
                'total_transactions': transaction_stats,
                'total_orders': StoreOrder.objects.filter(status='Completed').count(),
                'total_products': Product.objects.count(),
                'total_dropshippers': CustomUser.objects.filter(is_store_owner=True).count()
            }
            cache.set(cache_key, stats, 300)  # Cache for 5 minutes

        # Optimized transactions query
        transactions_queryset = PaystackWebhook.objects.select_related(
            'user', 'order'
        ).only(
            'id', 'reference', 'total_price', 'status', 'purpose', 'created_at',
            'user__first_name', 'user__last_name', 'user__email',
            'order__id', 'order__order_sn'
        )

        # Apply filters efficiently
        search_term = request.query_params.get('search', '').strip()
        if search_term:
            transactions_queryset = transactions_queryset.filter(
                Q(reference__icontains=search_term) |
                Q(user__email__icontains=search_term) |
                Q(order__order_sn__icontains=search_term)
            )
        
        # Simple filters
        for param in ['status', 'purpose']:
            value = request.query_params.get(param)
            if value:
                transactions_queryset = transactions_queryset.filter(**{param: value})
        
        # Amount range filters
        min_amount = request.query_params.get('min_amount')
        if min_amount:
            transactions_queryset = transactions_queryset.filter(total_price__gte=min_amount)
            
        max_amount = request.query_params.get('max_amount')
        if max_amount:
            transactions_queryset = transactions_queryset.filter(total_price__lte=max_amount)

        # Paginate and serialize
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(transactions_queryset, request)
        serializer = AdminTransactionSerializer(page, many=True)
        
        return Response({
            'stats': stats,
            'transactions': paginator.get_paginated_response(serializer.data).data
        }, status=drf_status.HTTP_200_OK)
    
class DropshipperAnalyticsView(APIView):
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination

    def get(self, request):
        # Optimized single query with all calculations
        dropshippers = CustomUser.objects.filter(
            is_store_owner=True
        ).select_related('owners').annotate(
            company_name=F('owners__name'),
            total_products=Count(
                'owners__pricings',
                filter=Q(owners__pricings__product__is_available=True),
                distinct=True
            ),
            total_revenue=Coalesce(
                Sum('owners__store_orders__total_price',
                    filter=Q(owners__store_orders__status='Completed')),
                Value(0.00)
            ),
            active_status=Case(
                When(last_login__gte=timezone.now() - timezone.timedelta(days=30), 
                     then=Value('Active')),
                default=Value('Inactive'),
                output_field=CharField()
            )
        ).only(
            'id', 'first_name', 'last_name', 'email', 'last_login',
            'owners__name'
        )

        # Apply search filter
        search_term = request.query_params.get('search', '').strip()
        if search_term:
            dropshippers = dropshippers.filter(
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(owners__name__icontains=search_term)
            )

        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            if status_filter == 'Active':
                dropshippers = dropshippers.filter(
                    last_login__gte=timezone.now() - timezone.timedelta(days=30)
                )
            else:
                dropshippers = dropshippers.filter(
                    Q(last_login__lt=timezone.now() - timezone.timedelta(days=30)) |
                    Q(last_login__isnull=True)
                )
            
        min_products = request.query_params.get('min_products')
        if min_products:
            dropshippers = dropshippers.filter(total_products__gte=min_products)
            
        min_revenue = request.query_params.get('min_revenue')
        if min_revenue:
            dropshippers = dropshippers.filter(total_revenue__gte=min_revenue)

        # Order by creation date
        dropshippers = dropshippers.order_by('-owners__created_at')

        # Paginate
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dropshippers, request)

        # Build optimized response
        response_data = [{
            'id': user.id,
            'name': user.get_full_name(),
            'email': user.email,
            'company_name': user.company_name,
            'total_products': user.total_products,
            'status': user.active_status,
            'revenue': str(user.total_revenue),
            'last_seen': user.last_login.isoformat() if user.last_login else None
        } for user in page]

        return paginator.get_paginated_response(response_data)