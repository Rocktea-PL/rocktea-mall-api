from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status as drf_status
from django.db.models import (
    Count, Sum, Value, DecimalField, IntegerField, Q, F,
    When, Case, CharField
)
from django.db.models.functions import Coalesce
from order.pagination import CustomPagination
from order.models import StoreOrder, PaystackWebhook, Product
from mall.models import CustomUser
from admin_orders.serializers import AdminTransactionSerializer
from django.utils import timezone

class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination

    def get(self, request):
        completed_orders_filter = Q(status='Completed')

        total_transactions_agg = PaystackWebhook.objects.filter(
            purpose='order',
            status='Success'
        ).aggregate(
            total_amount=Coalesce(Sum('total_price'), Value(0), output_field=DecimalField()),
            total_count=Coalesce(Count('id'), Value(0), output_field=IntegerField())
        )

        stats = {
            'total_transactions': total_transactions_agg,
            'total_orders': StoreOrder.objects.filter(completed_orders_filter).count(),
            'total_products': Product.objects.count(),
            'total_dropshippers': CustomUser.objects.filter(
                is_store_owner=True
            ).count()
        }

        # Get paginated transactions instead of orders
        transactions_queryset = PaystackWebhook.objects.select_related(
            'user', 'order'
        ).order_by('-created_at')

        # Apply search parameter
        search_term = request.query_params.get('search', '').strip()
        if search_term:
            transactions_queryset = transactions_queryset.filter(
                Q(reference__icontains=search_term) |
                Q(user__email__icontains=search_term) |
                Q(order__order_sn__icontains=search_term) |
                Q(status__icontains=search_term) |
                Q(purpose__icontains=search_term) |
                Q(total_price__icontains=search_term)
            )
        
        # Apply filters
        status = request.query_params.get('status')
        if status:
            transactions_queryset = transactions_queryset.filter(status=status)
            
        purpose = request.query_params.get('purpose')
        if purpose:
            transactions_queryset = transactions_queryset.filter(purpose=purpose)
            
        min_amount = request.query_params.get('min_amount')
        if min_amount:
            transactions_queryset = transactions_queryset.filter(total_price__gte=min_amount)
            
        max_amount = request.query_params.get('max_amount')
        if max_amount:
            transactions_queryset = transactions_queryset.filter(total_price__lte=max_amount)

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
        # Get all dropshippers with optimized annotations
        dropshippers = CustomUser.objects.filter(
            is_store_owner=True
        ).select_related('owners').annotate(
            company_name=F('owners__name'),
            # Use the new related_name 'pricings'
            total_products=Count(
                'owners__pricings',
                distinct=True,
                filter=Q(owners__pricings__product__is_available=True)
            ),
            # Use the existing related_name 'store_orders' from StoreOrder model
            total_revenue=Coalesce(
                Sum(
                    'owners__store_orders__total_price',
                    filter=Q(owners__store_orders__status='Completed'),
                    output_field=DecimalField()
                ),
                Value(0.00),
                output_field=DecimalField()
            ),
            active_status=Case(
                When(last_login__gte=timezone.now() - timezone.timedelta(days=30), 
                then=Value('Active')),
                default=Value('Inactive'),
                output_field=CharField()
            ),
            last_seen=F('last_login')
        ).order_by('-owners__created_at')

        # Apply search parameter
        search_term = request.query_params.get('search', '').strip()
        if search_term:
            dropshippers = dropshippers.filter(
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(owners__name__icontains=search_term) |
                Q(active_status__icontains=search_term)
            )

        # Apply filters
        status = request.query_params.get('status')
        if status:
            dropshippers = dropshippers.filter(active_status=status)
            
        min_products = request.query_params.get('min_products')
        if min_products:
            dropshippers = dropshippers.filter(total_products__gte=min_products)
            
        min_revenue = request.query_params.get('min_revenue')
        if min_revenue:
            dropshippers = dropshippers.filter(total_revenue__gte=min_revenue)

        # Paginate results
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dropshippers, request)

        # Build response data
        response_data = [{
            'name': user.get_full_name(),
            'email': user.email,
            'company_name': user.company_name,
            'total_products': user.total_products,
            'status': user.active_status,
            'revenue': str(user.total_revenue),
            'last_seen': user.last_seen.isoformat() if user.last_seen else None
        } for user in page]

        return paginator.get_paginated_response(response_data)