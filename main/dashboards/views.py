from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status as drf_status
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce
from order.pagination import CustomPagination
from order.models import StoreOrder, PaystackWebhook
from mall.models import CustomUser, Product
from admin_orders.serializers import AdminTransactionSerializer
from django.core.cache import cache

class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination

    def get(self, request):
        try:
            # Cache dashboard stats for 5 minutes
            cache_key = "admin_dashboard_stats"
            stats = cache.get(cache_key)
            
            if not stats:
                # Get basic counts
                total_transactions = PaystackWebhook.objects.filter(
                    purpose='order', status='Success'
                ).count()
                
                total_amount = PaystackWebhook.objects.filter(
                    purpose='order', status='Success'
                ).aggregate(amount=Sum('total_price'))['amount'] or 0
                
                stats = {
                    'total_transactions': {
                        'total_count': total_transactions,
                        'total_amount': float(total_amount)
                    },
                    'total_orders': StoreOrder.objects.filter(status='Completed').count(),
                    'total_products': Product.objects.count(),
                    'total_dropshippers': CustomUser.objects.filter(is_store_owner=True).count()
                }
                cache.set(cache_key, stats, 300)

            # Get transactions with basic filtering
            transactions_queryset = PaystackWebhook.objects.select_related('user', 'order')

            # Apply search filter
            search_term = request.query_params.get('search', '').strip()
            if search_term:
                transactions_queryset = transactions_queryset.filter(
                    Q(reference__icontains=search_term) |
                    Q(user__email__icontains=search_term)
                )
            
            # Apply status filter
            status_filter = request.query_params.get('status')
            if status_filter:
                transactions_queryset = transactions_queryset.filter(status=status_filter)
            
            # Apply purpose filter
            purpose_filter = request.query_params.get('purpose')
            if purpose_filter:
                transactions_queryset = transactions_queryset.filter(purpose=purpose_filter)

            # Order by created date
            transactions_queryset = transactions_queryset.order_by('-created_at')

            # Paginate and serialize
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(transactions_queryset, request)
            serializer = AdminTransactionSerializer(page, many=True)
            
            return Response({
                'stats': stats,
                'transactions': paginator.get_paginated_response(serializer.data).data
            }, status=drf_status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Failed to fetch dashboard stats',
                'details': str(e)
            }, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class DropshipperAnalyticsView(APIView):
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination

    def get(self, request):
        try:
            # Get dropshippers with basic info
            dropshippers = CustomUser.objects.filter(
                is_store_owner=True
            ).select_related('owners')

            # Apply search filter
            search_term = request.query_params.get('search', '').strip()
            if search_term:
                dropshippers = dropshippers.filter(
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term) |
                    Q(email__icontains=search_term)
                )

            # Order by date joined
            dropshippers = dropshippers.order_by('-date_joined')

            # Paginate
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(dropshippers, request)

            # Build response data
            response_data = []
            for user in page:
                try:
                    # Get store info safely
                    company_name = user.owners.name if hasattr(user, 'owners') and user.owners else 'N/A'
                    
                    # Calculate basic metrics
                    total_products = 0
                    total_revenue = 0
                    
                    if hasattr(user, 'owners') and user.owners:
                        total_products = user.owners.pricings.count()
                        completed_orders = user.owners.store_orders.filter(status='Completed')
                        total_revenue = sum(order.total_price for order in completed_orders)
                    
                    # Determine status
                    
                    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
                    status = 'Active' if user.last_login and user.last_login >= thirty_days_ago else 'Inactive'
                    
                    response_data.append({
                        'id': user.id,
                        'name': user.get_full_name(),
                        'email': user.email,
                        'company_name': company_name,
                        'total_products': total_products,
                        'status': status,
                        'revenue': str(total_revenue),
                        'last_seen': user.last_login.isoformat() if user.last_login else None
                    })
                except Exception as e:
                    # Skip problematic records
                    continue

            return paginator.get_paginated_response(response_data)
            
        except Exception as e:
            return Response({
                'error': 'Failed to fetch dropshipper analytics',
                'details': str(e)
            }, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)